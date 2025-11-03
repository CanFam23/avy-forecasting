import pandas as pd

from datetime import timedelta

from src import REQ_COLS, EXP_COLS

def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        if c in ['time','point_id','fxx','valid_time']:
            continue
            
        min_val = -10
        max_val = 1000
        
        bad_vals = df[(df[c] > max_val) | (df[c] < min_val)]

        if bad_vals.shape[0] != 0:
            for index, row in bad_vals.iterrows():
                # Get data from prev and next hours
                prev = df[(df['time'] == row['time'] - timedelta(hours=1)) & (df['point_id'] == row['point_id'])]
                next = df[(df['time'] == row['time'] + timedelta(hours=1)) & (df['point_id'] == row['point_id'])]

                if index == 0:
                    # First row, only next row exists
                    df.loc[index, c] = next[c].values[0]
                elif index == df.shape[0] - 1:
                    # Last row, only previous row exists
                    df.loc[index, c] = prev[c].values[0]
                else:
                    # Middle rows, average of previous and next
                    df.loc[index, c] = (next[c].values[0] + prev[c].values[0]) / 2 # type: ignore
            print(f"Replaced {bad_vals.shape[0]} major outliers in col {c}")
    return df

def validate_df(df: pd.DataFrame):
    if df.empty:
        raise AttributeError("Given DataFrame is empty!")
    
    for req_col in REQ_COLS:
        if req_col not in df.columns:
            raise KeyError(f"{REQ_COLS} not a column in given DataFrame!")