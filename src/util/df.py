import pandas as pd

from src import REQ_COLS, EXP_COLS

def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        if c in ['time','point_id','fxx','valid_time','sde']:
            continue
            
        min_val = -1000
        max_val = 1000
        
        bad_vals = df[(df[c] > max_val) | (df[c] < min_val)]

        if bad_vals.shape[0] != 0:
            for index, row in bad_vals.iterrows():
                if index == 0:
                    # First row, only next row exists
                    df.loc[index, c] = df.loc[index + 1, c]
                elif index == df.shape[0] - 1:
                    # Last row, only previous row exists
                    df.loc[index, c] = df.loc[index - 1, c]
                else:
                    # Middle rows, average of previous and next
                    df.loc[index, c] = (df.loc[index - 1, c] + df.loc[index + 1, c]) / 2 # type: ignore
            print(f"Replaced {bad_vals.shape[0]} major outliers in col {c}")
    return df

def validate_df(df: pd.DataFrame):
    if df.empty:
        raise AttributeError("Given DataFrame is empty!")
    
    for req_col in REQ_COLS:
        if req_col not in df.columns:
            raise KeyError(f"{REQ_COLS} not a column in given DataFrame!")