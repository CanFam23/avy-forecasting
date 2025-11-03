import os
import sys
import shutil
import warnings
from datetime import datetime, timedelta
from multiprocessing import Process, Queue
from typing import Optional, Union
from tkinter import messagebox

import geopandas as gpd
import herbie
import pandas as pd
from herbie.fast import FastHerbie

from src.util.df import remove_outliers, validate_df
from src.config import REQ_COLS, EXP_COLS, COORDS_FP

class HerbieFetcher():
    def __init__(self, output_file_dir, output_file_name, error_file_path, date_file_path, verbose = False, show_times = False):
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
        
        merged["fxx"] = (merged["step"].dt.components["hours"] == 1).astype(int)
        
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
                   remove_herbie_dir = False, remove_output_dir = False) -> None:
        if remove_herbie_dir:
            self.__remove_herbie_dir()
        if remove_output_dir:
            resp = messagebox.askyesno("Delete output file", f"Are you sure you want to delete {self.output_file_path}?")
            if not resp:
                sys.exit()
            self.__remove_output_file()
        
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
            
            if self.verbose:
                print(f"Appended data to {self.output_file_path} between {start}-{end}")
            if self.show_times:
                print(f"Finished whole process for {start}-{end} in {datetime.now()-s_time} (Total runtime: {datetime.now()-runtime})")
                
            with open(self.date_file_path, mode="w") as file:
                file.write(end.strftime("%m/%d/%Y %H:%M:%S"))
  
    def refetch_data(self, regs: list[str], fxx:list[int], coords: gpd.GeoDataFrame):
        """Attempts to refetch missing data found in `self.output_file_path`. Missing data is determined by
        1. Finding the min and max times in the output file, and creating a range of hourly dates between them (excluding June-September)
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
        
        # Load output data
        output_data = pd.read_csv(self.output_file_path)
        output_data['time'] = pd.to_datetime(output_data['time'])
        
        missing_hours = self.get_missing_hours(output_data)
        
        # Get rows with missing data
        times = [pd.to_datetime(t) for t in output_data[output_data.isna().any(axis=1)]['time'].drop_duplicates().to_list()]
        
        times += missing_hours
        
        if len(times) == 0:
            print(f"No missing dates found for {self.output_file_path}")
            return
        else:
            print(f"Found {len(times)} hours either missing or have missing data in {self.output_file_path}")
        
        times = sorted(times)
        i = 0

        # Make intervals from missing data
        while i < len(times)-1:
            start_time = times[i]
            end_time = start_time
            # Get the end time for current interval
            while i+1 < len(times)-1 and times[i+1] == end_time + timedelta(hours=1):
                end_time = times[i+1]
                i += 1
                
            missing_date_ranges.append((start_time,end_time))
            i += 1
        
        # Check last spot in case it was missed
        if len(times) > 0 and len(missing_date_ranges) == 0 or times[-1] != missing_date_ranges[-1][1]:
            missing_date_ranges.append((times[-1], times[-1]))
                
        # Resave data without missing values as they will get replaced hopefully
        output_data = output_data.dropna()
        output_data.drop_duplicates(inplace=True)
        output_data.sort_values(by='time',inplace=True)
        output_data.to_csv(self.output_file_path, index=False)
        
        self.fetch_data(regs=regs, fxx=fxx, coords=coords, intervals=missing_date_ranges)
        
        output_data = pd.read_csv(self.output_file_path)
        output_data['time'] = pd.to_datetime(output_data['time'])
        
        missing_hours = self.get_missing_hours(output_data)
        
        for hour in missing_hours:
            self.interpolate_missing_time(hour)
            
    def get_missing_hours(self, df):
        # Make range of dates from min to max time in output data
        dates = pd.date_range( df['time'].min(), df['time'].max(), freq='1h').to_list()

        # Remove summer months
        for i in range(len(dates)-1, 0, -1):
            if dates[i].month in [6,7,8,9]:
                dates.pop(i)

        # Get missing hours in output data
        missing_hours = list(set(dates)-set(df['time'].to_list()))
        
        return missing_hours
        
    def interpolate_missing_time(self, t: datetime):
        if self.verbose:
            print(f'Interpolating {t}')
        
        # Load output data
        output_data = pd.read_csv(self.output_file_path)
        output_data['time'] = pd.to_datetime(output_data['time'])
        
        validate_df(output_data)
        
        points = [int(n) for n in output_data['point_id'].unique()]
        fxxs = [int(n) for n in output_data['fxx'].unique()]

        # New data is the average of the hour before and after it
        new_rows = []
        for point in points:
            for fxx in fxxs:
                vals = output_data[((output_data['time'] == t + timedelta(hours=1)) | (output_data['time'] == t - timedelta(hours=1))) & (output_data['fxx'] == fxx) & (output_data['point_id'] == point)]
                
                if vals.shape[0] < 2:
                    warnings.warn(f"Missing nearby data for {t} - point_id {point} - fxx {fxx}")
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
        output_data = pd.concat([output_data] + new_rows, ignore_index=True)
        output_data.sort_values(by='time',inplace=True)
        output_data.drop_duplicates(inplace=True)
        output_data.to_csv(self.output_file_path, index=False)

    def split_data(self, split_seasons: bool = False):
        output_data = pd.read_csv(self.output_file_path)
        output_data['time'] = pd.to_datetime(output_data['time'])
        
        validate_df(output_data)
        
        remove_outliers(output_data)
        
        points = [n for n in output_data['point_id'].unique()]
        fxxs = [n for n in output_data['fxx'].unique()]
        
        point_strs = [str(int(n)) for n in points]
        fxx_strs = [str(int(n)) for n in fxxs]
        
        output_path = f"{self.output_file_dir}/{output_data['time'].min().strftime('%Y-%m-%d_%H')}_{output_data['time'].max().strftime('%Y-%m-%d_%H')}_{'_'.join(point_strs)}_{'_'.join(fxx_strs)}"
        
        os.makedirs(output_path, exist_ok=True)
        
        for point in points:
            for fxx in fxxs:
                filtered_df = output_data[(output_data['point_id'] == point) & (output_data['fxx'] == fxx)]
                filtered_df = filtered_df.drop_duplicates()
                
                if split_seasons:
                    min_year = filtered_df['time'].min().year
                    max_year = filtered_df['time'].max().year
                    years = [y for y in range(min_year, max_year, 1)]
                    
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
    error_file = "herbie_error_log.txt"
    date_path = "date_log.txt"
        
    if os.path.exists(date_path):
        with open(date_path, 'r') as file:
            time = file.readline()
            start_date = datetime.strptime(time, "%m/%d/%Y %H:%M:%S")
        print(f"Loaded start time from file: {start_date}")
    else:
        start_date = datetime(2020, 10, 1, 0, 0)  # start date
    n_days = 365 * 2  # Number of days

    fac_coords = gpd.read_file("../data/FAC/zones/grid_coords_subset.geojson")
    # fac_coords = fac_coords[fac_coords['zone_name'] == 'Whitefish']
    # test_coords = fac_coords.iloc[0:10,:].copy()
    test_coords = fac_coords.iloc[:,:].copy()

    test_coords = test_coords.rename(columns={'lat':'latitude','lon':'longitude'})

    surf_reg = r":(?:TMP|SNOD|PRATE|APCP|.*WRF|RH|ASNOW):surface"
    m2_reg = r":(?:TMP|RH):2 m"
    wind_reg = r":WIND|GRD:10 m above"
    regs = [surf_reg,m2_reg,wind_reg]

    fxx = [1]
    
    hf = HerbieFetcher(output_path, "grid_subset_weather_retry.csv", error_file,date_path, show_times=True)
    # hf.split_data(split_seasons=True)
    # hf.refetch_data(regs, fxx, test_coords)
    hf.fetch_data(regs = regs, 
                  fxx = fxx, 
                  coords=test_coords, 
                  start_date=start_date, 
                  n_days=n_days, remove_herbie_dir=True)
    
    print(f"Total time {datetime.now() - start_time}")