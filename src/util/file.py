import os
from datetime import datetime

import geopandas as gpd
import pandas as pd

from src.config import COORDS_FP, SNO_FP
from src.util.df import validate_df, remove_outliers

from src.util.geo import find_elevation

def csv_to_smet(df: pd.DataFrame, data_source: str, output_file_path: str, output_file_name: str):
    validate_df(df)
    
    df = remove_outliers(df)
    
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
        "si10":"VW",
        "max_10si":"VW_MAX",
        "wdir10":"DW",
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
    return {
        "id":station_id,
        "lat":station_coords['lat'].values[0],
        "lon":station_coords['lon'].values[0],
        "alt":station_altitude
    }
            
def smet_to_csv(data_source: str, output_file_path: str,output_file_name: str) -> None:
    data = []
    with open(data_source, "r") as file:
        line = file.readline().strip().split()
                
        while line != ['[DATA]']:
            if "station_id" in line:
                station_id = int(line[2][:3])
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
    df['altitude'] = altitude # type: ignore
    df['slope_angle'] = slope_angle # type: ignore
    df['slope_azi'] = slope_azi # type: ignore
    
    df.drop_duplicates(inplace=True)
    
    os.makedirs(output_file_path, exist_ok=True)
    
    df.to_csv(os.path.join(output_file_path,output_file_name), index=False)
    
def update_sno(id: int, lat: float, lon: float, altitude: float, year: int = 2020) -> None:
    """Updates sno files to work with given data. Since all sno files contain the same data
    besides the given parameters, this avoids having to have multiple sno files for each station.

    Args:
        id (int): Id of station
        lat (float): latitude of station
        lon (float): longitude of station
        altitude (float): altitude of station
        year (int, optional): Start year of simulation. Defaults to 2020.
    """
    for fn in os.listdir(SNO_FP):
        fp = os.path.join(SNO_FP, fn)

        # Read sno file
        with open(fp, 'r') as sno_file:
            lines = sno_file.readlines()
            lines = [l.strip().split() for l in lines]
        
        for i in range(len(lines)):
            match lines[i][0]: 
                case 'station_id':
                    lines[i][2] = str(id)
                case 'station_name':
                    lines[i][2] = f"s_{id}" # type: ignore
                case 'latitude':
                    lines[i][2] = str(lat)
                case 'longitude':
                    lines[i][2] = str(lon)
                case 'altitude':
                    lines[i][2] = str(altitude)
                case 'ProfileDate':
                    lines[i][2] = pd.Timestamp(year=year, month=10, day=1).isoformat()
        new_name = fn.split(".")[0]
        
        if len(new_name) == 3:
            new_name = str(id)
        else:
            new_name = str(id) + new_name[-1]
        new_name += ".sno"
        
        new_fp = os.path.join(SNO_FP, new_name)
        
        os.rename(fp, new_fp)
        
        for i in range(len(lines)):
            lines[i] = " ".join(lines[i]) + "\n" # type: ignore
            
        with open(new_fp, 'w') as new_sno:
            new_sno.writelines(lines) # type: ignore