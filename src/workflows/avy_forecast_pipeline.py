import os
import pickle
from datetime import datetime, timedelta

import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv

from src.config import COORDS_SUBSET_FP, REGS
from src.herbie.herbie_fetch import HerbieFetcher
from src.sim.simulation import run_simulation
from src.util.model import get_averages, get_elevation_band

load_dotenv()

DEFAULT_SNO_PATH = f"SNOWPATH = {os.getenv('DEFAULT_SNO_PATH')}\n"

def comebine_data(past_data_fp: str, forecast_data_fp: str, day: datetime, output_fp: str) -> None:
    """Combines past data csv and forecasted data csv into one csv file. 

    Args:
        past_data_fp (str): File path to csv with past data
        forecast_data_fp (str): File path to csv with forecast data
        day (datetime): Day of forecast data
        output_fp (str): Where to output combined file (Path and name)
    """
    past_df = pd.read_csv(past_data_fp)
    past_df['time'] = pd.to_datetime(past_df['time'])
    
    forecast_data = pd.read_csv(forecast_data_fp)

    # Get forecast data for point with id in past df
    forecast_data = forecast_data[forecast_data['point_id'] == past_df['point_id'].unique()[0]].drop_duplicates()
    forecast_data['valid_time'] = pd.to_datetime(forecast_data['valid_time'])
    forecast_data['time'] = forecast_data['valid_time']
    
    # Filter past df for all data up to day
    past_df = past_df[past_df['time'] <= day]
    
    # Filter forecast data for given day only
    forecast_data[forecast_data['time'].dt.date == day.date()]
    
    combined_df = pd.concat([past_df, forecast_data])
    
    start_date = combined_df['time'].min()
    
    # Assert combined df isn't missing any hours #TODO prob need to make this check better
    assert combined_df.shape[0] == ((day - start_date + timedelta(days=1)).days * 24 + 1), f"combined df ({combined_df.shape[0]}) doesn't have expected number of hours ({((day - start_date + timedelta(days=1)).days * 24 + 1)})"

    combined_df.to_csv(output_fp, index=False)
    
if __name__ == "__main__":
    process_start = datetime.now()
    
    fac_coords = gpd.read_file(COORDS_SUBSET_FP).rename(columns={'lat':'latitude','lon':'longitude'})

    with open("data/models/best_model_2.pkl", "rb") as file:
        model = pickle.load(file)
    
    start_time = datetime.now()
    
    output_file_dir = "data/fetched"
    output_file_name = "weather_25-26.csv"
    error_file = "logs/operational_error_log.txt"
    date_file = "logs/operatioanl_error_log.txt"
    
    sim_output_path = "data/ops25_26"

    hf = HerbieFetcher(
        output_file_dir=output_file_dir,
        output_file_name=output_file_name,
        error_file_path=error_file,
        date_file_path=date_file,
        show_times=True
    )
    
    day = datetime(2025, 12,8)
        
    sid = str(fac_coords['id'].unique()[0])
    
    # Fetch any missing data up to day
    fetched = hf.fetch_missing_season_data(2025,day,REGS,[1],fac_coords)

    if fetched:
        hf.split_data(output_dir_name="2526_split", split_seasons=True)
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
    
    prev_day = day - timedelta(days=1)
            
    # Fetch forecasted data for current day in 6-hour intervals
    print(f"Fetching current day forecast {day}")
    for i in range(0,23,6):
        hf.fetch_data(
            REGS, 
            fxx=[i for i in range(i+1, i+7)],
            coords=fac_coords,
            intervals=[(day, day)],
            remove_herbie_dir=True)
    hf.split_data(output_dir_name="2526_forc_split", split_seasons=True)
    
    print(f"Finished fetching forecast data in {datetime.now() - start_time}")
    
    start_time = datetime.now()
    
    # Run simulation for each point and then make predictions
    for id in fac_coords['id'].unique():
        print(f"Predicting for #{id}")
        
        comebine_data(f"data/fetched/2526_split/weather_2025-2025_p{id}_fxx1/weather_2025_p{id}_fxx1.csv", "data/fetched/forecast_25-26.csv", day, f"data/sim_temp/{id}.csv")
        
        run_simulation("data/sim_temp", "data/input/avyIO.ini", output_dir="data/sim_fetch")
        
        os.remove(os.path.join("data/sim_temp",f"{id}.csv"))
    
        sim_data = pd.read_csv(f"data/sim_fetch/snow_2025-2025_p{id}_fxx1.csv")
        sim_data['timestamp'] = pd.to_datetime(sim_data['timestamp'])
    
        sim_data = sim_data[sim_data['timestamp'].dt.date == day.date()] # type: ignore
        
        if sim_data.empty:
            print(f"{id} missing data for {day.date()}, skipping")
            continue

        df = sim_data.drop(columns=['MS_Soil_Runoff', 'TSS_meas'])
        
        daily_avg, removed_cols = get_averages(df)

        preds = model.predict(daily_avg)
        
        daily_avg = pd.concat([daily_avg, removed_cols], axis=1)
        
        predictions = daily_avg[['date','id', 'slope_angle', 'slope_azi',
       'altitude']].copy(deep=True)
        
        predictions['predicted_danger'] = preds
        
        predictions.to_csv("data/ops25_26/all_predictions.csv", index=False, header=False, mode='a')
        
    pred_file = pd.read_csv("data/ops25_26/all_predictions.csv")
    pred_file = pred_file.drop_duplicates()
    pred_file.to_csv("data/ops25_26/all_predictions.csv", index=False)
    
    for file in os.listdir("data/sim_fetch"):
        os.remove(os.path.join("data/sim_fetch", file))
        
    print(f"Finished making predictions in {datetime.now() - start_time}")

    pred_file = pd.merge(pred_file, fac_coords, on=['id'], how='inner').drop(columns=["latitude","longitude","geometry"])
    pred_file['elevation_band'] = pred_file['altitude'].apply(get_elevation_band)
        
    day_data = pred_file.groupby(by=["date","zone_name", "elevation_band", "slope_angle"])['predicted_danger'].agg(lambda x: x.mode().max()).reset_index()
    day_data['slope_angle'] = day_data['slope_angle'].apply(lambda x: "flat" if x == 0 else "slope")
    day_data.to_csv("data/ops25_26/day_predictions.csv",index=False)
    
    print(f"Process completed in {datetime.now() - process_start}")
