import numpy as np
from numpy.typing import ArrayLike
import pandas as pd

from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, root_mean_squared_error, mean_absolute_error, mean_squared_error

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
    print(f"Accuracy {acc:.2f}")
    print(f"MSE: {mean_squared_error(y_a, y_p)}")
    print(f"RMSE: {root_mean_squared_error(y_a, y_p)}")
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

def prep_data(df: pd.DataFrame, danger_df: pd.DataFrame, danger_col: str, replace_missing: bool =True, replace_val: float = 0, change_danger: bool = False, exclude_cols: list[str] = ['date','id', 'danger_level']) -> tuple[pd.DataFrame, pd.Series]:
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
        tuple[pd.DataFrame, pd.Series]: X and y dataframes / series.
    """
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    if replace_missing:
        df = df.loc[:, ~(df == -999).all()]
    
    # Find daily average of all columns
    daily_avg = df.groupby(pd.Grouper(key='timestamp', freq='D')).mean()
    
    if replace_missing:
        daily_avg = daily_avg.replace(-999, replace_val)
        
    avgs = daily_avg.reset_index()

    # Filter dates to those only found in danger_df
    avgs = avgs[avgs['timestamp'].isin(danger_df['date'])]
    
    avgs = avgs.rename(columns={"timestamp":"date"})
    
    # Merge dfs
    data = pd.merge(avgs, danger_df, on='date', how='outer')
    data = data.rename(columns={danger_col:"danger_level"})
    
    if change_danger:
        data['danger_level'] = data['danger_level'].apply(change_dangers)

    X = data[[c for c in data.columns if c not in exclude_cols]]
    y = data['danger_level']
    
    return X,y