import os
import subprocess

import pandas as pd

from src.util.file import csv_to_smet, smet_to_csv, update_sno
    
def run_simulation(file_path: str, ini_file_path: str, output_dir: str) -> bool:
    output_files = []
    s_id = "none"
    failed = False
    for file in os.listdir(file_path):
        print(f"Running simulation on {file}")
        
        df = pd.read_csv(os.path.join(file_path, file))
        fxx = int(df['fxx'].unique()[0])
        id = int(df['point_id'].unique()[0])
        s_id = str(id)
        df['time'] = pd.to_datetime(df['time'])
        smet_name = f"{file.split('.')[0]}.smet"
        station_data = csv_to_smet(df, file, "data/input", smet_name)
        
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
        
        update_sno(station_data["id"], station_data["lat"], station_data["lon"], station_data["alt"])
        
        # Run snowpack
        result = subprocess.run(["/Applications/Snowpack/bin/snowpack", "-b", df['time'].min().isoformat(), "-e", df['time'].max().isoformat(), "-c", "/Users/nickclouse/Desktop/senior-proj/avy-forecasting/data/input/avyIO.ini"], capture_output=True, text=True)

        # Codes -11 and 0 usually mean SNOWPACK ran successfully
        if result.returncode not in [-11,0]:
            print(result.stderr)
            print(result.stdout)
            failed = True
        
        # Convert smet data to csv
        for of in os.listdir(f"data/output"):
            if of.find(str(id)) != -1 and of.find("smet") != -1:
                # print(of)
                smet_to_csv(f"data/output/{of}","data/sim_output",f"{file.split('.')[0]}_{of.split('.')[0]}_output.csv")
                output_files.append(os.path.join("data/sim_output",f"{file.split('.')[0]}_{of.split('.')[0]}_output.csv"))
        
        for file in os.listdir("data/output"):
            if s_id in file:
                os.remove(os.path.join("data/output",file))
                # print(f"Removed {file}")
                
    if not failed:
        merged_df = pd.DataFrame()
        for file in output_files:
            fdf = pd.read_csv(file)
            merged_df = pd.concat([merged_df, fdf])

        merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'])
        merged_df.sort_values(by='timestamp',inplace=True)
        merged_df.dropna(inplace=True)
        merged_df.drop_duplicates(inplace=True)
    
        os.makedirs(output_dir, exist_ok=True)

        merged_df.to_csv(f"{output_dir}/snow_{merged_df['timestamp'].min().year}-{merged_df['timestamp'].max().year}_p{id}_fxx{fxx}.csv",index=False)         # type: ignore

    # Clean up files
    for file in os.listdir("data/input"):
        if s_id in file and ".smet" in file:
            os.remove(os.path.join("data/input",file))
            # print(f"Removed {file}")
            
    for file in os.listdir("data/sim_output"):#output_files:
        if s_id in file:
            os.remove(os.path.join("data/sim_output",file))
            # print(f"Removed {file}")
    return failed
    
            
if __name__ == "__main__":
    
    output_path = "data/ops25_26"
    os.makedirs(output_path, exist_ok=True)
    
    fp = "data/fetched/2526_split"
    for f in os.listdir(fp):
        
        id = f.split("p")[1][:3]
        
        # found = False
        # for t in os.listdir(output_path):
        #     if f"p{id}" in t:
        #         found = True
        #         break
        
        # if found:
        #     print(f'Skipping {f}')
        #     continue
        
        failed = run_simulation(os.path.join(fp,f),"data/input/avyIO.ini", output_path)
        if failed:
            print(f"{f} failed")
            with open("sim_log.txt", "a") as file:
                file.write(f + "\n")
        break
