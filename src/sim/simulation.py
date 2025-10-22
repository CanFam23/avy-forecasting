import os
import subprocess
from datetime import datetime

import geopandas as gpd
import pandas as pd

from src.config import COORDS_FP
from src.util.df import validate_df, remove_outliers

from src.util.geo import find_elevation

def csv_to_smet(df: pd.DataFrame, data_source: str, output_file_path: str, output_file_name: str) -> None:
    validate_df(df)
    
    remove_outliers(df)
    
    df['time'] = pd.to_datetime(df['time'])
    
    station_id = int(df['point_id'].unique()[0])
    
    coords = gpd.read_file(COORDS_FP)
    
    df['r2'] = df['r2'] / 100 # Convert to decimal
    df['prate'] = df['prate'] * 60 * 60 # kg/m2/s = mm/s, so * 60 == mm/min * 60 = mm/hr
    
    var_map = {
        "time":"timestamp",
        "t":"TSG",
        "t2m":"TA",
        "r2":"RH",
        "gust":"VW_MAX",
        "max_10si":"VW",
        "sdswrf":"ISWR",
        "suswrf":"RSWR",
        "sdlwrf":"ILWR",
        "sulwrf":"OLWR",
        "prate":"PINT",
        "tp":"PSUM",
        "sde":"HS"
    }

    df = df[var_map.keys()].copy()
    df.rename(mapper=var_map, inplace=True, axis=1)
    df.sort_values(by='timestamp',inplace=True)
    df.drop_duplicates(subset=['timestamp'],keep="first",inplace=True)
    
    station_coords = coords[coords['id'] == station_id]
    
    station_altitude = find_elevation(station_id,station_coords['lat'].values[0],station_coords['lon'].values[0])

    os.makedirs(output_file_path, exist_ok=True)
    
    # df['DW'] = 0

    with open(os.path.join(output_file_path, output_file_name), "w") as file:
        file.write("SMET 1.1 ASCII\n")
        file.write("[HEADER]\n")
        file.write(f"station_id = {station_id}\n")
        file.write(f"station_name = s_{station_id}\n")
        file.write(f"latitude = {station_coords['lat'].values[0]}\n")
        file.write(f"longitude = {station_coords['lon'].values[0]}\n")
        file.write(f"altitude = {station_altitude}\n")
        file.write(f"epsg = 4326\n")
        file.write("tz = 0\n")
        file.write("nodata = -999\n")
        file.write(f"source = {data_source}\n")
        file.write(f"creation = {datetime.now().isoformat()}\n")
        file.write(f"fields = {' '.join(df.columns)}\n")
        
        file.write(f"[DATA]\n")
        
        for index, row in df.iterrows():
            row.iloc[0] = row.iloc[0].isoformat()
            row = [str(d) for d in row]
            file.write(' '.join(row) + "\n")
            
def smet_to_csv(data_source: str, output_file_path: str,output_file_name: str) -> None:
    data = []
    with open(data_source, "r") as file:
        c = 0
        line = file.readline().strip().split()
                
        while line != ['[DATA]']:
            if "station_id" in line:
                station_id = int(line[2])
            elif "fields" in line:
                col_names = line[2:]
            elif "altitude" in line:
                altitude = float(line[2])
            elif "slope_angle" in line:
                slope_angle = float(line[2])
            elif "slope_azi" in line:
                slope_azi = float(line[2])
            line = file.readline().strip().split()
            
            if not line:
                break
            
        if not station_id or not col_names: # type: ignore
            raise ValueError("No station_id or field names found!")
        
        if not altitude or slope_angle or slope_azi: # type: ignore
            raise ValueError("One of altitude, slope angle, or slope azimuth is missing!")
            
        while line:
            line = file.readline().strip().split()
            for i in range(len(line)):
                try:
                    line[i] = float(line[i]) # type: ignore
                except ValueError:
                    line[i] = line[i]
            data.append(line)
            
    df = pd.DataFrame(data=data, columns=col_names)
    df['id'] = station_id
    df['altitude'] = altitude
    df['slope_angle'] = slope_angle # type: ignore
    df['slope_azi'] = slope_azi # type: ignore
    
    os.makedirs(output_file_path, exist_ok=True)
    
    df.to_csv(os.path.join(output_file_path,output_file_name), index=False)
    
def run_simulation(file_path: str, ini_file_path: str) -> None:
    output_files = []
    for file in os.listdir(file_path):
        print(f"Running simulation on {file}")
        
        df = pd.read_csv(os.path.join(file_path, file))
        fxx = int(df['fxx'].unique()[0])
        id = int(df['point_id'].unique()[0])
        df['time'] = pd.to_datetime(df['time'])
        smet_name = f"{file.split('.')[0]}.smet"
        csv_to_smet(df, file, "data/input", smet_name)
        
        # Put input file in ini file so SNOWPACK uses correct file
        with open(ini_file_path, 'r') as ini_file:
            lines = ini_file.readlines()
        for i in range(len(lines)):
            if 'STATION1' in lines[i]:
                lines[i] = f'STATION1 = {smet_name}\n'
                break
        with open(ini_file_path, "w") as ini_file:
            ini_file.writelines(lines)
        
        # Run snowpack
        result = subprocess.run(["/Applications/Snowpack/bin/snowpack", "-b", df['time'].min().isoformat(), "-e", df['time'].max().isoformat(), "-c", "/Users/nickclouse/Desktop/senior-proj/avy-forecasting/data/input/avyIO.ini"], capture_output=True, text=True)

        # Codes -11 and 0 usually mean SNOWPACK ran successfully
        if result.returncode not in [-11,0]:
            print(result.stderr)
            print(result.stdout)
        
        # Convert smet data to csv
        smet_to_csv(f"data/output/{id}_Avy_forc.smet","data/sim_output",f"{file.split('.')[0]}_output.csv")
        output_files.append(os.path.join("data/sim_output",f"{file.split('.')[0]}_output.csv"))
            
    merged_df = pd.DataFrame()
    for file in output_files:
        fdf = pd.read_csv(file)
        merged_df = pd.concat([merged_df, fdf])

    merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'])
    merged_df.sort_values(by='timestamp',inplace=True)
    merged_df.dropna(inplace=True)
    
    os.makedirs("data/training_data", exist_ok=True)

    merged_df.to_csv(f"data/training_data/snow_{merged_df['timestamp'].min().year}-{merged_df['timestamp'].max().year}_p{id}_fxx{fxx}.csv",index=False)         # type: ignore

            
if __name__ == "__main__":
    fp = "../data/FAC/2020-10-01_00_2025-06-01_00_159_160_0_1/weather_2020-2025_p159_fxx1"
    run_simulation(fp,"data/input/avyIO.ini")