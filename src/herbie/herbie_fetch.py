import os
import shutil
import sys
import warnings
from datetime import datetime, timedelta
from multiprocessing import Process, Queue
from tkinter import messagebox
from typing import Optional, Union

import geopandas as gpd
import pandas as pd

import herbie
from herbie.fast import FastHerbie
from src.config import COORDS_FP, EXP_COLS, REQ_COLS
from src.util.df import remove_outliers, validate_df


class HerbieFetcher():
    def __init__(self, output_file_dir, output_file_name, error_file_path, date_file_path, verbose = False, show_times = False, remove_output_file=False):
        if not os.path.exists(output_file_dir):
            print(f"Created path '{output_file_dir}'")
            os.makedirs(output_file_dir, exist_ok=True)
        
        self.output_file_name = output_file_name
        self.output_file_dir = output_file_dir
        self.output_file_path = os.path.join(self.output_file_dir,self.output_file_name)
        self.error_file_path = error_file_path
        self.date_file_path = date_file_path
        self.verbose = verbose
        self.show_times = show_times
        
        if remove_output_file:
            resp = messagebox.askyesno("Delete output file", f"Are you sure you want to delete {self.output_file_path}?")
            if not resp:
                sys.exit()
            self.__remove_output_file()

    def get_data(self,dates:list[datetime], fxx: Union[int, list[int]], search_regex: str, coords: pd.DataFrame, queue: Queue) -> None:
        """Retrieves the data specified in the given search regex for the given dates, fxx, and coords. Adds the retrieved data to the given queue\n
        ### Note
        This function should mainly be used in multiprocessing, as it adds the data to a queue after it's retrieved. 

        Args:
            dates (list[datetime]): Dates to get data for.
            fxx (Union[int, list[int]]): fxx to get data for.
            search_regex (str): Search regex for Herbie
            coords (pd.DataFrame): Coords to get data for
            queue (Queue): Queue to add data to
        """
        if self.verbose:
            print(f"fetching data for {min(dates)}-{max(dates)}, regex: {search_regex}")
            
        s_time = datetime.now()
        
        fh = FastHerbie(DATES=dates, fxx=fxx, max_processes=10) # type: ignore
        data_set = fh.xarray(search=search_regex)
        
        if "WIND" in search_regex:
            data_set = data_set.herbie.with_wind()
        
        if data_set:
            point_ds = data_set.herbie.pick_points(coords)
            
            # xarray datasets can't be pickled, so convert to dataframe
            queue.put(point_ds.to_dataframe())
            
            if self.verbose or self.show_times:
                print(f"Finished fetching data in {datetime.now() - s_time}, regex: {search_regex}")
        else:
            warnings.warn(f"No data found for {dates}, regex: {search_regex}")
        
    def mutate_save_data(self, data_frames: list[pd.DataFrame]) -> bool:
        """Combines the data frames in the given list together, selects the needed columns defined in `exp_cols`, and saves the data to the `output_file_path`\n
        If the data frame has more than 23 columns, the data frames will be combined horizontally (stacked on top of each other) since
        regexs that are searching for a large amount of data have their data split into 2 fetches of `get_data` to improve the fetch speed.

        Args:
            data_frames (list[pd.DataFrame]): List of data frames to save

        Returns:
            bool: `True` if the data was successfully saved, `False` otherwise
        """
        s_time = datetime.now()
        
        if len(data_frames) == 0:
            warnings.warn("data_frames can't be empty!")
            return False
            
        merged = pd.DataFrame()
        other_dfs = []
        
        # This combines datasets that are from long regexs split in 2 
        for i in range(len(data_frames)):
            if data_frames[i].shape[1] >= 20: # Dfs from regexes have more columns
                merged = pd.concat([merged, data_frames[i].reset_index()])
            else:
                other_dfs.append(data_frames[i])
                
        # Combine all dfs together
        for i in range(len(other_dfs)):
            suffixes = (f"_{i}",f"_{i}{i}") # Unique suffixes to prevent errors on combining multiple dfs
            data_set = other_dfs[i]

            merged = pd.merge(merged, data_set,how="outer",on=["valid_time","time","step","point_id"], suffixes=suffixes)
        
        merged.drop_duplicates(inplace=True)
        
        merged["fxx"] = 1#(merged["step"].dt.components["hours"] == 1).astype(int) # type: ignore
        
        keep_cols = [c for c in merged.columns if c in EXP_COLS]
        filtered_df = merged[keep_cols]
        
        df_cols = filtered_df.columns.to_list()
        missing_cols = []
        for c in EXP_COLS:
            if c not in df_cols or filtered_df[c].isna().any():
                missing_cols.append(c)
        if len(missing_cols) > 0:
            warnings.warn(f"Missing {','.join(missing_cols)}")
            return False

        filtered_df = filtered_df[EXP_COLS] # Reorder exp_cols
        
        if os.path.exists(self.output_file_path) and os.path.getsize(self.output_file_path) > 0:
            filtered_df.to_csv(self.output_file_path,index=False,header=False,mode='a')
        else: # Add header if file is empty
            filtered_df.to_csv(self.output_file_path,index=False,header=True,mode='a')
            
        if self.verbose or self.show_times:
            print(f"Finished saving data in {datetime.now()-s_time}")
        return True
        
    def fetch_data(self, regs: list[str], fxx:list[int], coords: gpd.GeoDataFrame, start_date: Optional[datetime] = None, 
                   n_days: Optional[int] = None, intervals: Optional[list[tuple[datetime, datetime]]] = [], 
                   remove_herbie_dir = False) -> None:
        if remove_herbie_dir:
            self.__remove_herbie_dir()
        
        runtime = datetime.now()

        if start_date and n_days:
            # Prepare 6-hour intervals for each day
            intervals = []
            for day in range(n_days):
                day_start = start_date + timedelta(days=day)
                
                if day_start > datetime.now() - timedelta(days=1):
                    warnings.warn(f"{day_start} is too close to current day")
                    break
                
                # Skip summer months
                if day_start.month >= 6 and day_start.month <= 9:
                    continue
                
                for i in range(4):  # 4 intervals of 6 hours each
                    interval_start = day_start + timedelta(hours=6*i)
                    interval_end = interval_start + timedelta(hours=6)
                    intervals.append((interval_start, interval_end))
        elif intervals and len(intervals) != 0:
            for start,end in intervals:
                if not isinstance(start, (datetime, pd.Timestamp)) or not isinstance(end, (datetime, pd.Timestamp)) or start > end:
                    raise ValueError(f"Given intervals list must be a list of tuples, where each tuple contains a start and end date")
        elif (not intervals or len(intervals) == 0) and not start_date and not n_days:
            raise ValueError(f"Either start_date and n_days or a list of intervals must be given!")
        
        if not intervals:
            raise ValueError("No intervals given")
                
        # Get data in intervals
        for start, end in intervals:
            s_time = datetime.now()

            DATES = pd.date_range(start=start, end=end, freq='1h')
            
            data = []
            
            # Utilize multiprocessing, doubles the speed
            try:
                queue = Queue()
                    
                processes = []
                for r in regs:
                    # Split up regexs that are big 
                    if len(r) > 20 and len(DATES) > 1:
                        p = Process(target=self.get_data, kwargs={"dates": DATES[:len(DATES)//2], "fxx":fxx, "search_regex":r, "coords":coords, "queue":queue})
                        processes.append(p)
                        p = Process(target=self.get_data, kwargs={"dates": DATES[len(DATES)//2:], "fxx":fxx, "search_regex":r, "coords":coords, "queue":queue})
                        processes.append(p)
                    else:
                        p = Process(target=self.get_data, kwargs={"dates": DATES, "fxx":fxx, "search_regex":r, "coords":coords, "queue":queue})
                        processes.append(p)
                    
                fetch_start_time = datetime.now()
                for p in processes:
                    p.start()
                    
                # Get data and put it into a list so it can be saved.
                # With larger data sets, the processes often get stuck 
                # I think it's caused by the queue's background thread blocking indefinitely
                # My work around is as soon as all the data is received, the queue is closed and the background thread(s) is joined 
                while len(data) < len(processes): 
                    # safeguard in case something in the processes method causes it to never add data
                    if datetime.now() - fetch_start_time > timedelta(seconds = 75):
                        raise Exception("More than 60 seconds has passed since processes starting fetching data!")
                    data.append(queue.get(True, timeout=120))
                    
                # Calling close before join thread ensures all data is flushed to the queue before the bg thread is joined
                queue.close()
                queue.join_thread()
                    
                for p in processes:
                    # Extra safeguard against indefinite blocking, but with above code the process should never timeout (hopefully)
                    p.join(timeout=30)
                    if p.exitcode and p.exitcode != 0:
                        warnings.warn(f"Process {p.pid} finished with exit code {p.exitcode}")
                    
            except Exception as e:
                warnings.warn(f"Error parsing {start}-{end}, not saving data. \n Error: {e}")
                with open(self.error_file_path, mode="a") as file:
                    file.write(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{start},{end},{e}\n')
                continue

            # Attempt to save data
            if not self.mutate_save_data(data):
                with open(self.error_file_path, mode="a") as file:
                    file.write(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{start},{end}, missing data\n')
                continue
            
            # Remove any dupplicates and sort by time cols
            output_data = pd.read_csv(self.output_file_path).drop_duplicates().sort_values(by=['time','valid_time'])
            output_data.to_csv(self.output_file_path, index=False)
            
            if self.verbose:
                print(f"Appended data to {self.output_file_path} between {start}-{end}")
            if self.show_times:
                print(f"Finished whole process for {start}-{end} in {datetime.now()-s_time} (Total runtime: {datetime.now()-runtime})")
                
            with open(self.date_file_path, mode="w") as file:
                file.write(end.strftime("%m/%d/%Y %H:%M:%S"))         
  
    def refetch_data(self, regs: list[str], fxx:list[int], coords: gpd.GeoDataFrame):
        """Attempts to refetch missing data found in `self.output_file_path`. Missing data is determined by
        
        1. Finding the min and max times in the error output file, and creating a range of hourly dates between them (excluding June-September)
        2. Checking the output df for hours not found 
        3. Checking the output df for hours with missing data.\n
        The missing hours are then converted to date/time ranges where possible to allow for efficient fetching.
        If again no data is found for an hour after refetching, interpolation is attempted for the hour by calling `self.interpolate_missing_time()`.

        ### NOTE
        The `coords` parameter **MUST** have 2 columns titled `latitude` and `longitude`. 

        Args:
            regs (list[str]): Regexs to search for
            fxx (list[int]): fxx to get
            coords (gpd.GeoDataFrame): Coords to get data for
        """
        missing_date_ranges = []
        
        # Look at error file for time ranges that failed
        with open(self.error_file_path, "r") as file:
            lines = file.readlines()

        str_format = "%Y-%m-%d %H:%M:%S"
            
        for line in lines:
            line = line.split(",")[1:3]
            missing_date_ranges.append((datetime.strptime(line[0], str_format),datetime.strptime(line[1], str_format)))

        if len(missing_date_ranges) > 0:
            self.fetch_data(regs=regs, fxx=fxx, coords=coords, intervals=missing_date_ranges)

        # Load output data
        output_data = pd.read_csv(self.output_file_path)
        output_data['time'] = pd.to_datetime(output_data['time'])
        
        still_missing = []
        
        with open(self.error_file_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                line_split = line.split(",")
                # If data isn't found in output df and data hasn't attempted to be refetched yet, append to still missing
                if not output_data['time'].isin([datetime.strptime(line_split[1],str_format)]).any() and (len(line_split) == 4 and line_split[3] == "still missing data after retry"):
                    line_split = "still missing data after retry\n"
                    still_missing.append(",".join(line_split))
                    
        # Rewrite missing dates to error file 
        with open(self.error_file_path, "w") as file:
            file.writelines(still_missing)
        
        missing_hours = self.get_missing_hours(output_data,output_data['time'].min(), output_data['time'].max())
        
        # Get rows with missing data
        times = [pd.to_datetime(t) for t in output_data[output_data.isna().any(axis=1)]['time'].drop_duplicates().to_list()]
        
        times += missing_hours
    
        if len(times) == 0:
            print(f"No missing dates found for {self.output_file_path}")
            return
        else:
            print(f"Found {len(times)} hours either missing or have missing data in {self.output_file_path}")
        
        # Interpolate remaining missing times
        for hour in sorted(times):
            output_data = self.interpolate_missing_time(output_data,hour)
                
        # Resave data
        output_data = output_data.dropna()
        output_data.drop_duplicates(inplace=True)
        output_data.sort_values(by='time',inplace=True)
        output_data.to_csv(self.output_file_path, index=False)
        
    def fetch_missing_forecast_data(self, season: int, day: datetime,regs: list[str], coords: gpd.GeoDataFrame) -> bool:
        """Fetch missing forecast data up to and including day. This fetches the data 
        for hours 1-23 from forecast hour (fxx) 0 of each day.

        Args:
            season (int): Season to get data for (Start year of season)
            day (datetime): Last day to check for missing data
            regs (list[str]): Regular expressions to search for
            coords (gpd.GeoDataFrame): Coordinates to pull data for.=

        Returns:
            bool: True if the data was successfully fetched, False otherwise
        """        
        season_start = datetime(season,12,1,0,0,0)
        
        fetched_df = pd.read_csv(self.output_file_path).drop_duplicates()
        
        validate_df(fetched_df)
        
        fetched_df['valid_time'] = pd.to_datetime(fetched_df['valid_time'], format='mixed')
        
        missing_hours = []
        
        # Check each id for missing hours
        # This will lead to data for one hour to be pulled for all ids
        # But the duplicates get removed after pulling is finished
        num_hours = (day - fetched_df['valid_time'].min()).total_seconds() // 3600 # Number of hours between min in df and given day
        for id in fetched_df['point_id'].unique():
            id_df = fetched_df[fetched_df['point_id'] == id]
            if id_df.shape[0] != num_hours + 24:
                missing_hours += self.get_missing_hours(fetched_df, season_start, day + timedelta(days=1), time_col='valid_time')
        
        if len(missing_hours) == 0:
            print("No missing hours found")
            return False
        
        # Remove duplicates and sort missing hours
        missing_hours = sorted(list(set(missing_hours)))
        
        print(f"Found {len(missing_hours)} missing hours")
        
        i = 0
        
        missing_hour_ranges = []

        # Create time ranges of 1-6 hours 
        while i < len(missing_hours)-1:
            start_time = missing_hours[i]
            end_time = start_time
            # Get the end time for current interval
            while i+1 <= len(missing_hours)-1 and missing_hours[i+1] == end_time + timedelta(hours=1) and end_time - start_time <= timedelta(hours=6):
                end_time = missing_hours[i+1]
                i += 1

            missing_hour_ranges.append((start_time,end_time))
            i += 1
        
        # Sometimes the last hour in missing_hours is skipped or the above logic doesn't work if there is only one hour in it
        if len(missing_hours) > 0 and len(missing_hour_ranges) == 0 or missing_hours[-1] != missing_hour_ranges[-1][1]:
            missing_hour_ranges.append((missing_hours[-1], missing_hours[-1]))

        # This function always fetches data for time 00:00:00, and uses ranges for the fxx since its forecasted data
        for interval in missing_hour_ranges:
            start_ts = interval[0]
            if start_ts.hour == 0:
                start_date = start_ts - timedelta(days=1)
                start_fxx = 24
            else:
                start_date = pd.to_datetime(start_ts.date())
                start_fxx = start_ts.hour
            
            end_ts = interval[1]
            if end_ts.hour == 0:
                end_date = end_ts - timedelta(days = 1)
                end_fxx = 24
            else:
                end_date = pd.to_datetime(end_ts.date())
                end_fxx = end_ts.hour

            self.fetch_data(
                regs, 
                fxx=[i for i in range(start_fxx, end_fxx+1)],
                coords=coords,
                intervals=[(start_date,end_date)],
                remove_herbie_dir=True)
        return True
        
    def fetch_missing_season_data(self, season: int, day: datetime,regs: list[str], fxx:list[int], coords: gpd.GeoDataFrame):
        season_start = datetime(season,10,1,0,0,0)
        
        fetched_df = pd.read_csv(self.output_file_path).drop_duplicates()
        
        validate_df(fetched_df)
        
        fetched_df['time'] = pd.to_datetime(fetched_df['time'], format='mixed')

        missing_hours = []
        
        # Check each id for missing hours
        # This will lead to data for one hour to be pulled for all ids
        # But the duplicates get removed after pulling is finished
        num_hours = (day - fetched_df['time'].min()).total_seconds() // 3600 # Number of hours between min in df and given day
        for id in fetched_df['point_id'].unique():
            id_df = fetched_df[fetched_df['point_id'] == id]
            if id_df.shape[0] != num_hours + 24:
                missing_hours += self.get_missing_hours(fetched_df, season_start, day)
        
        if len(missing_hours) == 0:
            print("No missing hours found")
            return False
        
        # Remove duplicates and sort missing hours
        missing_hours = sorted(list(set(missing_hours)))
        
        print(f"Found {len(missing_hours)} missing hours")
        
        i = 0
        
        missing_hour_ranges = []
        
        # Create time ranges of 1-6 hours 
        while i < len(missing_hours)-1:
            start_time = missing_hours[i]
            end_time = start_time
            # Get the end time for current interval
            while i+1 < len(missing_hours)-1 and missing_hours[i+1] == end_time + timedelta(hours=1) and end_time - start_time <= timedelta(hours=6):
                end_time = missing_hours[i+1]
                i += 1
                
            missing_hour_ranges.append((start_time,end_time))
            i += 1
        
        # Sometimes the last hour in missing_hours is skipped or the above logic doesn't work if there is only one hour in it
        if len(missing_hours) > 0 and len(missing_hour_ranges) == 0 or missing_hours[-1] != missing_hour_ranges[-1][1]:
            missing_hour_ranges.append((missing_hours[-1], missing_hours[-1]))
            
        self.fetch_data(regs, fxx, coords, intervals=missing_hour_ranges, remove_herbie_dir=True)
        
        return True
           
    def get_missing_hours(self, df, min, max, time_col='time'):
        # Make range of dates from min to max time in output data
        dates = pd.date_range( min, max, freq='1h').to_list()

        # Remove summer months
        for i in range(len(dates)-1, 0, -1):
            if dates[i].month in [6,7,8,9]:
                dates.pop(i)

        # Get missing hours in output data
        missing_hours = list(set(dates)-set(df[time_col].to_list()))
        
        return missing_hours
        
    def interpolate_missing_time(self, df: pd.DataFrame, t: datetime):
        if self.verbose:
            print(f'Interpolating {t}')
        
        validate_df(df)
        
        points = [int(n) for n in df['point_id'].unique()]
        fxxs = [int(n) for n in df['fxx'].unique()]

        # New data is the average of the hour before and after it
        new_rows = []
        for point in points:
            for fxx in fxxs:
                vals = df[((df['time'] == t + timedelta(hours=1)) | (df['time'] == t - timedelta(hours=1))) & (df['fxx'] == fxx) & (df['point_id'] == point)]
                
                if vals.shape[0] < 2:
                    warnings.warn(f"Missing nearby data for {t} - point_id {point} - fxx {fxx} nearby: {vals.shape[0]}")
                    continue

                new_entry = pd.DataFrame({
                    'time': [t],
                    'valid_time': [t + timedelta(hours=fxx)],
                    'point_id': [point],
                    'fxx': [fxx]
                })

                for i in range(vals.shape[1]):
                    if vals.columns[i] in REQ_COLS:
                        continue
                    new_entry[vals.columns[i]] = (vals.iloc[0,i] + vals.iloc[1,i]) / 2 # type: ignore
                new_entry = new_entry[vals.columns.to_list()]
                new_rows.append(new_entry)
               
        # Add new rows 
        df = pd.concat([df] + new_rows, ignore_index=True)
        return df

    def split_data(self, output_dir_name: str = "", split_seasons: bool = False, time_col = 'time'):
        output_data = pd.read_csv(self.output_file_path)
        output_data[time_col] = pd.to_datetime(output_data[time_col], format='mixed')
        if time_col != 'time':
            output_data['time'] = pd.to_datetime(output_data['time'], format='mixed')

        validate_df(output_data)
        
        output_data = remove_outliers(output_data,time_col)
        
        points = [n for n in output_data['point_id'].unique()]
        fxxs = [n for n in output_data['fxx'].unique()]
        
        point_strs = [str(int(n)) for n in points]
        fxx_strs = [str(int(n)) for n in fxxs]
        
        if output_dir_name == "":
            output_path = f"{self.output_file_dir}/{output_data['time'].min().strftime('%Y-%m-%d_%H')}_{output_data['time'].max().strftime('%Y-%m-%d_%H')}_{'_'.join(point_strs)}_{'_'.join(fxx_strs)}"
        else:
            output_path = os.path.join(self.output_file_dir, output_dir_name)
            
        os.makedirs(output_path, exist_ok=True)
        
        for point in points:
            for fxx in fxxs:
                filtered_df = output_data[(output_data['point_id'] == point) & (output_data['fxx'] == fxx)]
                filtered_df = filtered_df.drop_duplicates()
                
                if split_seasons:
                    min_year = filtered_df['time'].min().year
                    max_year = filtered_df['time'].max().year
                    years = [y for y in range(min_year, max_year+1, 1)]
                    
                    split_output_folder = f"weather_{min_year}-{max_year}_p{int(point)}_fxx{int(fxx)}"
                    
                    split_output_path = os.path.join(output_path,split_output_folder)
                    
                    os.makedirs(split_output_path, exist_ok=True)

                    for year in years:
                        start_date = datetime(year, 10,1)
                        end_date = datetime(start_date.year + 1, 6,1)
                        
                        curr_df = filtered_df[(filtered_df['time'] >= start_date) & (filtered_df['time'] < end_date)]

                        curr_df.to_csv(f"{split_output_path}/weather_{year}_p{int(point)}_fxx{int(fxx)}.csv",index=False)
                else:
                    filtered_df.to_csv(f"{output_path}/weather_p{int(point)}_fxx{int(fxx)}.csv",index=False)
                
    def __remove_herbie_dir(self):
        herbie_data_dir = os.path.expanduser("~/data")

        if os.path.exists(herbie_data_dir) and 'hrrr' in os.listdir(herbie_data_dir):
            shutil.rmtree(herbie_data_dir)
            print(f"Removed herbie data dir.")
          
    def __remove_output_file(self):
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)
            if self.verbose:
                print(f"{self.output_file_path} deleted.")
        
if __name__ == "__main__":
        
    start_time = datetime.now()
    
    output_path = "data/fetched"
    error_file = "logs/herbie_error_log.txt"
    date_path = "logs/date_log.txt"
        
    if os.path.exists(date_path):
        with open(date_path, 'r') as file:
            time = file.readline()
            start_date = datetime.strptime(time, "%m/%d/%Y %H:%M:%S")
        print(f"Loaded start time from file: {start_date}")
    else:
        start_date = datetime(2025, 10, 1, 0, 0)  # start date
    n_days = 365  # Number of days

    fac_coords = gpd.read_file("../data/FAC/zones/grid_coords_subset.geojson")
    # fac_coords = fac_coords[fac_coords['zone_name'] == 'Whitefish']
    # test_coords = fac_coords.iloc[0:10,:].copy()
    test_coords = fac_coords.iloc[:,:].copy()

    test_coords = test_coords.rename(columns={'lat':'latitude','lon':'longitude'})

    fxx = [1]
    
    hf = HerbieFetcher(output_path, "weather_25-26.csv", error_file,date_path, show_times=True)
    # hf.split_data(split_seasons=True)
    # hf.refetch_data(REGS, fxx, test_coords)
    # hf.fetch_data(regs = REGS, 
    #               fxx = fxx, 
    #               coords=test_coords, 
    #               start_date=start_date, 
    #               n_days=n_days, remove_herbie_dir=True)
    
    print(f"Total time {datetime.now() - start_time}")