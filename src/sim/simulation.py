import os
import subprocess

import pandas as pd

from src.util.file import csv_to_smet, smet_to_csv
    
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
        
        print(f"Running SNOWPACK id {id} fxx {fxx} {df['time'].min().isoformat()} to {df['time'].max().isoformat()} ")
        
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
    merged_df.drop_duplicates(inplace=True)
    
    os.makedirs("data/training_data", exist_ok=True)

    merged_df.to_csv(f"data/training_data/snow_{merged_df['timestamp'].min().year}-{merged_df['timestamp'].max().year}_p{id}_fxx{fxx}.csv",index=False)         # type: ignore

            
if __name__ == "__main__":
    fp = "../data/FAC/2020-10-01_00_2025-06-01_00_159_160_0_1/weather_2020-2025_p160_fxx0"
    run_simulation(fp,"data/input/avyIO.ini")