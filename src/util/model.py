import numpy as np
from numpy.typing import ArrayLike
import pandas as pd

from sklearn.metrics import accuracy_score,balanced_accuracy_score, confusion_matrix, ConfusionMatrixDisplay, root_mean_squared_error, mean_absolute_error, mean_squared_error

F_TO_M = 3.281

ELEV_MAP = {
    "lower": (0, 5000 / F_TO_M),
    "middle": (5000 / F_TO_M, 6500 / F_TO_M),
    "upper": (6500 / F_TO_M, (6500 / F_TO_M) * 2) # No mountains above 13,000 in mt...
}

def get_elevation_band(altitude):
    for key in ELEV_MAP.keys():
        if ELEV_MAP[key][0] <= altitude < ELEV_MAP[key][1]:
            return key
        
    raise ValueError(f"{altitude} not in a elevation band!")

def eval_model(y_a: ArrayLike, y_p: ArrayLike, plot: bool = False, norm: bool = False) -> None:
    """Evaluates the given data by computing the accuracy, MSE, RMSE, and MAE, and optionally displays
    a confusion matrix (Which can be normalized).

    Args:
        y_a (ArrayLike): Actual y values
        y_p (ArrayLike): Predicted y values
        plot (bool, optional): Whether to plot confusion matrix. Defaults to False.
        norm (bool, optional): Whether to normalized confusion matrix. Defaults to False.
    """
    acc = accuracy_score(y_a, y_p)
    bacc = balanced_accuracy_score(y_a,y_p)
    print(f"Accuracy {acc:.2f}")
    print(f"Balanced Accuracy {bacc:.2f}")
    # print(f"MSE: {mean_squared_error(y_a, y_p)}")
    # print(f"RMSE: {root_mean_squared_error(y_a, y_p)}")
    print(f"MAE: {mean_absolute_error(y_a, y_p)}")

    if plot:
        labels = np.unique(y_a)

        # Reorder labels so they are in the same order
        y_order = labels[::-1]
        x_order = labels 
        
        if norm:
            cm = confusion_matrix(y_a, y_p, normalize="true", labels=np.unique(y_a))
            cm_reordered = cm[np.ix_(y_order, x_order)]
            
            disp = ConfusionMatrixDisplay(confusion_matrix=cm_reordered,
                              display_labels=x_order)
            disp.plot(cmap='Blues', values_format='.2f')

            disp.ax_.set_yticks(np.arange(len(y_order)))
            disp.ax_.set_yticklabels(y_order)
            disp.ax_.set_title("Normalized Confusion Matrix")
        else:
            cm = confusion_matrix(y_a, y_p)
            cm_reordered = cm[np.ix_(y_order, x_order)]

            disp = ConfusionMatrixDisplay(confusion_matrix=cm_reordered,
                              display_labels=x_order)
            disp.plot(cmap='Blues', values_format='d')

            disp.ax_.set_yticks(np.arange(len(y_order)))
            disp.ax_.set_yticklabels(y_order)
            disp.ax_.set_title("Confusion Matrix")
            
def change_dangers(danger):
    if danger >= 3:
        return 3
    return danger

def get_danger(row):
    """Helper function to get danger level based on elevation band"""
    return row[row['elevation_band']]

def prep_data(df: pd.DataFrame, danger_df: pd.DataFrame, replace_missing: bool =True, change_danger: bool = False, exclude_cols: list[str] = ['date','id', 'danger_level']) -> tuple[pd.DataFrame, pd.Series,pd.DataFrame]:
    """Prepares the given data for training / testing. This method does so by:
    1. Ensuring the timestamp col is in datetime format
    2. Replace missing values with `replace_val` if `replace_missing` is true
    3. Only includes data from dates found in `danger_df`
    4. merges `df` and `danger_df`
    5. Converts the merged df to a `X` df and a `y` series.

    Args:
        df (pd.DataFrame): DataFrame containing the input data.
        danger_df (pd.DataFrame): DataFrame containing the prediction data.
        danger_col (str): Name of column to get danger levels from.
        replace_missing (bool, optional): Whether to replace missing values. Defaults to True.
        replace_val (float, optional): Value to replace missing values with. Defaults to 0.
        change_danger (bool, optional): Whether to change the danger with `change_danger` method. Defaults to False.
        exclude_cols (list[str], optional): Columns to exclude in input data. Defaults to ['date','id', 'danger_level'].

    Returns:
        tuple[pd.DataFrame, pd.Series, pd.DataFrame]: X and y dataframes / series along with a dataframe of the columns removed.
    """
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.loc[:, ~(df == -999).all()]
    
    if replace_missing:
       df.replace(-999, np.nan)
    
    # Find daily average of all columns
    daily_avg = df.groupby(['id',pd.Grouper(key='timestamp', freq='D')]).mean()
    
    avgs = daily_avg.reset_index()

    # Filter dates to those only found in danger_df
    avgs = avgs[avgs['timestamp'].isin(danger_df['date'])]
    
    avgs = avgs.rename(columns={"timestamp":"date"})
    
    # Merge dfs
    data = pd.merge(avgs, danger_df, on='date', how='outer')
    
    data['elevation_band'] = data['altitude'].apply(get_elevation_band)
    
    data['danger_level'] = data.apply(get_danger, axis=1)
    
    if change_danger:
        data['danger_level'] = data['danger_level'].apply(change_dangers)

    extra_exclude_cols = ['danger_rating', 'lower',
       'upper', 'middle','id_y']
    X = data[[c for c in data.columns if c not in exclude_cols]]
    X = X[[c for c in X.columns if c not in extra_exclude_cols]]
    y = data['danger_level']
    excluded_cols = data[[c for c in data.columns if c  in exclude_cols]]
    
    return X,y, excluded_cols