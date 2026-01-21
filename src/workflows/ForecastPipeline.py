import os
import pickle
from datetime import datetime, timedelta, date
import sys
from typing import Union

import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv

from src.config import COORDS_SUBSET_FP, REGS
from src.herbie.herbie_fetch import HerbieFetcher
from src.sim.simulation import run_simulation
from src.util.model import get_averages, get_elevation_band

load_dotenv()

DEFAULT_SNO_PATH = f"SNOWPATH = {os.getenv('DEFAULT_SNO_PATH')}\n"

# Number of stations * number of virtual slopes
NUM_DAILY_PREDS = 33 * 5 

class ForecastPipeline():
    def comebine_data(self,past_data_fp: str, forecast_data_fp: str, day: datetime, output_fp: str) -> None:
        """Combines past data csv and forecasted data csv into one csv file. Past data is taken up to 
        the given day whule forecast data is taken for the given day. 

        Args:
            past_data_fp (str): File path to csv with past data
            forecast_data_fp (str): File path to csv with forecast data
            day (datetime): Day of forecast data
            output_fp (str): Where to output combined file (Path and name)
        """
        past_df = pd.read_csv(past_data_fp)
        past_df['time'] = pd.to_datetime(past_df['time'])
        
        missing_hours = self.get_missing_hours(past_df, past_df['time'].min(),day - timedelta(days=1))
        forecast_data = pd.read_csv(forecast_data_fp)

        # Get forecast data for point with id in past df
        forecast_data = forecast_data[forecast_data['point_id'] == past_df['point_id'].unique()[0]].drop_duplicates()
        forecast_data['valid_time'] = pd.to_datetime(forecast_data['valid_time'])
        forecast_data['time'] = forecast_data['valid_time']
        
        # Filter past df for all data up to day
        past_df = past_df[past_df['time'] <= day]

        # Filter forecast data for given day only
        forecast_data = forecast_data[forecast_data['time'].dt.date == day.date()]
        combined_df = pd.concat([past_df, forecast_data])
            
        missing_hours = self.get_missing_hours(combined_df, past_df['time'].min(),day)

        assert not missing_hours, f"Missing {missing_hours} for point {past_df['point_id'].unique()[0]}"
        assert combined_df['time'].max() == day.replace(hour=23), f"DataFrame has more hours than expected, Max date should be {day.replace(hour=23)}, got {combined_df['time'].max()}"
        
        combined_df.to_csv(output_fp, index=False)
        
    def get_missing_hours(self,df: pd.DataFrame,min: Union[pd.Timestamp, datetime, date],max: Union[pd.Timestamp, datetime, date]) -> list[pd.Timestamp]:
        """Gets the hours (In datetime form) missing in the given dataFrame, assuming it has a column named 'time' with hour
        indexed dates.

        Args:
            df (pd.DataFrame): DataFrame to check. Must have a hour indexed 'time' column.
            min (Union[pd.Timestamp, datetime, date]): Min value for date range
            max (Union[pd.Timestamp, datetime, date]): Max value for date range

        Returns:
            list[pd.Timestamp]: List of missing dates
        """
        
        # Make range of dates from min to max time in output data
        dates = pd.date_range( min, max, freq='1h').to_list()

        # Remove summer months
        for i in range(len(dates)-1, 0, -1):
            if dates[i].month in [6,7,8,9]:
                dates.pop(i)

        # Get missing hours in output data
        missing_hours = list(set(dates)-set(df['time'].to_list()))

        return missing_hours

    def get_missing_predictions(self,pred_fp: str , model_fp: str , fac_coords_fp: str ) -> None:
        """Simulate the snowpack and then predict for any day found with missing predictions.

        Args:
            pred_fp (str): File to save predictions to.
            model_fp (str): File where a model is stored that can be used to predict the danger.
            fac_coords_fp (str): File where point coordinates are stored.
        """
        # Load FAC coordinate file
        fac_coords = gpd.read_file(fac_coords_fp).rename(columns={'lat':'latitude','lon':'longitude'})

        # Load model
        with open(model_fp, "rb") as file:
            model = pickle.load(file)

        pred_df = pd.read_csv(pred_fp)
        pred_df['date'] = pd.to_datetime(pred_df['date'])

        pred_df_grouped = pred_df.groupby(by='date').size()

        # Get dates that have no predictions or not enough predictions
        dates_missing_sims = pred_df_grouped[pred_df_grouped != NUM_DAILY_PREDS]
        dates = set(pd.date_range( pred_df['date'].min(), datetime.now().date(), freq='1D').to_list())
        missing_dates = dates - set(dates_missing_sims.index)

        if not missing_dates:
            print("No missing predictions found")
            return
        
        # Run simulation for each missing date
        start_time = datetime.now()
        for day in missing_dates:
            # Run simulation for each point and then make predictions
            for id in fac_coords['id'].unique():
                print(f"Predicting for #{id}")
                
                self.comebine_data(f"data/fetched/2526_split/weather_2025-2026_p{id}_fxx1/weather_2025_p{id}_fxx1.csv", f"data/fetched/2526_forc_split/weather_2025-2026_p{id}_fxx1/weather_2025_p{id}_fxx1.csv", day, f"data/sim_temp/{id}.csv")
                    
                failed, file_name = run_simulation("data/sim_temp", "data/input/avyIO.ini", output_dir="data/sim_fetch")
                
                os.remove(os.path.join("data/sim_temp",f"{id}.csv"))
                
                if not file_name or failed:
                    print(f"Sim for {id} failed, skipping predictions")
                    continue
                        
                sim_data = pd.read_csv(file_name)
                sim_data['timestamp'] = pd.to_datetime(sim_data['timestamp'])
                
                if sim_data.empty:
                    print(f"{id} missing data for {day.date()}, skipping")
                    continue

                df = sim_data.drop(columns=['MS_Soil_Runoff', 'TSS_meas'])
                
                daily_avg, removed_cols = get_averages(df)

                # Make predictions
                preds = model.predict(daily_avg)
                predictions = pd.concat([daily_avg, removed_cols], axis=1)
                
                predictions['predicted_danger'] = preds
                
                predictions = predictions[predictions['date'].dt.date == day.date()] # type: ignore
                
                predictions.to_csv(pred_fp, index=False, header=not os.path.exists(pred_fp), mode='a')
            
            # Remove dups from prediction file
            pred_file = pd.read_csv(pred_fp)
            pred_file = pred_file.drop_duplicates()
            pred_file.to_csv(pred_fp, index=False)
            
            # Clean up
            for file in os.listdir("data/sim_fetch"):
                os.remove(os.path.join("data/sim_fetch", file))
                
            print(f"Finished making predictions in {datetime.now() - start_time}")

            pred_file = pd.merge(pred_file, fac_coords, on=['id'], how='inner').drop(columns=["latitude","longitude","geometry"])
            pred_file['elevation_band'] = pred_file['altitude'].apply(get_elevation_band)
            
            # Make single day predictions based on mode danger for that group
            day_data = pred_file.groupby(by=["date","zone_name", "elevation_band", "slope_angle"])['predicted_danger'].agg(lambda x: x.mode().max()).reset_index()
            day_data['slope_angle'] = day_data['slope_angle'].apply(lambda x: "flat" if x == 0 else "slope")
            day_data.to_csv("data/ops25_26/day_predictions.csv",index=False)

    def fetch_missing_weather_data(self,output_file_dir: str, output_file_name: str ,error_file: str ,date_fil: str, fac_coords_fp: str) -> None:
        start_time = datetime.now()

        fac_coords = gpd.read_file(fac_coords_fp).rename(columns={'lat':'latitude','lon':'longitude'})

        # HerbieFetcher for past data
        hf = HerbieFetcher(
            output_file_dir=output_file_dir,
            output_file_name=output_file_name,
            error_file_path=error_file,
            date_file_path=date_file,
            show_times=True
        )

        day = pd.to_datetime(datetime.now().date())
                
        print("Checking for missing season data")
        
        # Fetch any missing data up to day
        fetched = hf.fetch_missing_season_data(2025,day,REGS,[1],fac_coords)
        hf.split_data(output_dir_name="2526_split", split_seasons=True)
        if fetched:
            print(f"Finished fetching data in {datetime.now() - start_time}")

        start_time = datetime.now()
            
        # Fetch forecasted data 
        hf = HerbieFetcher(
            output_file_dir=output_file_dir,
            output_file_name="forecast_25-26.csv",
            error_file_path=error_file,
            date_file_path=date_file,
            show_times=True
        )
                    
        print(f"Fetching current day forecast {day}")
        fetched = hf.fetch_missing_forecast_data(2025,day,REGS,fac_coords)    
        hf.split_data(output_dir_name="2526_forc_split", split_seasons=True, time_col='valid_time')
        if fetched:
            print(f"Finished fetching forecast data in {datetime.now() - start_time}")

    def run_pipeline(self,output_file_dir: str,output_file_name: str,error_file: str,date_file: str,fac_coords_fp: str,pred_output_fp: str,model_fp: str) -> None:
        """
        Run the full data ingestion and prediction pipeline.

        This method first fetches any missing historical and forecast weather data
        for all forecast area coordinates, then simulates the snowpack and generates
        avalanche danger predictions for any dates with missing or incomplete
        predictions.

        Args:
            output_file_dir (str): Directory where fetched weather data files are written.
            output_file_name (str): Base filename for fetched historical weather data.
            error_file (str): Path to a file used for logging fetch errors.
            date_file (str): Path to a file tracking processed dates.
            fac_coords_fp (str): File path to forecast area coordinate data.
            pred_output_fp (str): File path where prediction outputs are stored/appended.
            model_fp (str): File path to the trained model used for predictions.
        """
        fp.fetch_missing_weather_data(
            output_file_dir,
            output_file_name,
            error_file,
            date_file,
            fac_coords_fp
        )

        fp.get_missing_predictions(
            pred_output_fp,
            model_fp,
            fac_coords_fp
        )

if __name__ == "__main__":
    process_start = datetime.now()
    
    start_time = datetime.now()
    output_file_dir = "data/fetched"
    output_file_name = "weather_25-26.csv"
    error_file = "logs/operational_error_log.txt"
    date_file = "logs/operatioanl_error_log.txt"
    
    pred_output_file = "data/ops25_26/all_predictions.csv"

    fp = ForecastPipeline()

    fp.run_pipeline(output_file_dir,output_file_name,error_file,date_file, COORDS_SUBSET_FP,pred_output_file,"data/models/best_model_4.pkl")

    print(f"Process completed in {datetime.now() - process_start}")
