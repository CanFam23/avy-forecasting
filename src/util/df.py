import logging
import pandas as pd

from datetime import timedelta

from src import REQ_COLS

logger = logging.getLogger(__name__)

def remove_outliers(df: pd.DataFrame, time_col: str = 'time') -> pd.DataFrame:
    """Removes outliers in each row of the given dataFrame. This is mainly used after pulling HRRR data as sometimes
    the data will be extremely unrealistice (Like 10,000 for temperature). All of the data should never be outside
    of -10 < x < 1000, so any of those 'bad' values get removed. 

    Args:
        df (pd.DataFrame): DataFrame to remove outliers from

    Returns:
        pd.DataFrame: Cleaned dataFrame
    """
    df = df.sort_values(by=time_col)
    for c in df.columns:
        if c in ['time','point_id','fxx','valid_time']:
            continue
            
        min_val = -10
        max_val = 1000
        
        bad_vals = df[(df[c] > max_val) | (df[c] < min_val)]

        if bad_vals.shape[0] != 0:
            for index, row in bad_vals.iterrows():
                # Get data from prev and next hours
                prev = df[(df[time_col] == row[time_col] - timedelta(hours=1)) & (df['point_id'] == row['point_id'])]
                next = df[(df[time_col] == row[time_col] + timedelta(hours=1)) & (df['point_id'] == row['point_id'])]

                if index == 0:
                    # First row, only next row exists
                    df.loc[index, c] = next[c].values[0] # type: ignore
                elif index == df.shape[0] - 1:
                    # Last row, only previous row exists
                    df.loc[index, c] = prev[c].values[0] # type: ignore
                else:
                    # Middle rows, average of previous and next
                    df.loc[index, c] = (next[c].values[0] + prev[c].values[0]) / 2 # type: ignore
            logger.info(f"Replaced {bad_vals.shape[0]} major outliers in col {c}")
    return df

def validate_df(df: pd.DataFrame):
    """Validates given dataFrame by ensuring all of the `REQ_COLS` are present.

    Args:
        df (pd.DataFrame): Dataframe to Validate

    Raises:
        AttributeError: If the dataFrame is empty
        KeyError: If a required column is not found in the dataFrame.
    """
    if df.empty:
        raise AttributeError("Given DataFrame is empty!")
    
    for req_col in REQ_COLS:
        if req_col not in df.columns:
            raise KeyError(f"{REQ_COLS} not a column in given DataFrame!")