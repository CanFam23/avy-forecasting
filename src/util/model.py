import numpy as np
from numpy.typing import ArrayLike
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import accuracy_score,balanced_accuracy_score, confusion_matrix, ConfusionMatrixDisplay, root_mean_squared_error, mean_absolute_error, mean_squared_error, classification_report

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

def eval_model(y_a: ArrayLike, y_p: ArrayLike, plot: bool = False, norm: bool = False, cr: bool = False) -> None:
    """Evaluates the given data by computing the accuracy, MSE, RMSE, and MAE, and optionally displays
    a confusion matrix (Which can be normalized).

    Args:
        y_a (ArrayLike): Actual y values
        y_p (ArrayLike): Predicted y values
        plot (bool, optional): Whether to plot confusion matrix. Defaults to False.
        norm (bool, optional): Whether to normalized confusion matrix. Defaults to False.
        cr: (bool, optional): Whether to print a classification report or not
    """    
    acc = accuracy_score(y_a, y_p)
    bacc = balanced_accuracy_score(y_a,y_p)
    print(f"Accuracy {acc:.2f}")
    print(f"Balanced Accuracy {bacc:.2f}")
    print(f"MAE: {mean_absolute_error(y_a, y_p)}")
    
    if cr:
        print("Classification Report:")
        print(classification_report(y_a, y_p, digits=2))

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
            disp.ax_.set_xticklabels([i+1 for i in x_order])
            disp.ax_.set_yticklabels([i+1 for i in y_order])
            disp.ax_.set_title("Normalized Confusion Matrix")
        else:
            cm = confusion_matrix(y_a, y_p)
            cm_reordered = cm[np.ix_(y_order, x_order)]

            disp = ConfusionMatrixDisplay(confusion_matrix=cm_reordered,
                              display_labels=x_order)
            disp.plot(cmap='Blues', values_format='d')

            disp.ax_.set_yticks(np.arange(len(y_order)))
            disp.ax_.set_xticklabels([i+1 for i in x_order])
            disp.ax_.set_yticklabels([i+1 for i in y_order])
            disp.ax_.set_title("Confusion Matrix")
            
def plot_performance(df):
    data = {"name": [],
        "elevation": [],
        "value": []}
    
    for z in df['zone_name'].unique():
        for e in df['elevation_band'].unique():
                fdf = df[(df['elevation_band'] == e) & (df['zone_name'] == z)]
                if not fdf.empty:
                    ac = accuracy_score(fdf['danger_level'],fdf['predicted'])
                    data['name'].append(z)
                    data['elevation'].append(e)
                    data['value'].append(ac)
                else:
                    data['name'].append(z)
                    data['elevation'].append(e)
                    data['value'].append(None)


    pdf = pd.DataFrame(data)

    # order elevations
    elev_order = ["lower", "middle", "upper"]
    pdf["elevation"] = pd.Categorical(pdf["elevation"], categories=elev_order, ordered=True)

    pivot = pdf.pivot(index="elevation", columns="name", values="value")

    # plotting outline with text in each cell
    fig, ax = plt.subplots()

    cax = ax.imshow(pivot.values, aspect='auto')

    # Add text labels
    for i in range(pivot.shape[0]):            # rows
        for j in range(pivot.shape[1]):        # columns
            val = pivot.iloc[i, j]
            if pd.notna(val):
                ax.text(j, i, f"{val:.2%}", ha='center', va='center',color='white' if val < 0.78 else 'black') # type: ignore
            else:
                ax.text(j, i, "n/a", ha='center', va='center')

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    fig.colorbar(cax)
    plt.show()
            
def change_dangers(danger):
    if danger >= 3:
        return 3
    return danger

def get_danger(row):
    """Helper function to get danger level based on elevation band"""
    return row[row['elevation_band']]

def prep_data(df: pd.DataFrame, danger_df: pd.DataFrame, coords_geodf:pd.DataFrame, replace_missing: bool = True, change_danger: bool = False, exclude_cols: list[str] = ['date','id', 'danger_level']) -> tuple[pd.DataFrame, pd.Series,pd.DataFrame]:
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
    daily_avg = df.groupby(['id','slope_angle','slope_azi',pd.Grouper(key='timestamp', freq='D')]).mean()

    avgs = daily_avg.reset_index()

    # Filter dates to those only found in danger_df
    avgs = avgs[avgs['timestamp'].isin(danger_df['date'])]
    
    avgs = avgs.rename(columns={"timestamp":"date"})
    
    # Merge average data and coordinate data to match ids and zones
    data = pd.merge(avgs, coords_geodf, left_on="id", right_on="id")

    # Ensure zone names match
    data['zone_name'] = data['zone_name'].str.lower()
    danger_df = danger_df.rename(columns={"forecast_zone_id":"zone_name"})
    data['zone_name'] = data['zone_name'].replace("glacier/flathead","flathead")
    
    # Merge data and danger levels
    data = pd.merge(data, danger_df, on=['date','zone_name'], how='inner')
    
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

def get_averages(df: pd.DataFrame,
              remove_cols = ["id","slope_angle","slope_azi","date","altitude"]):
    df = df.rename(columns={"timestamp":"date"})
    
    if not all(rc in df.columns for rc in remove_cols):
        print([rc for rc in remove_cols if rc not in df.columns])
        
    assert all(rc in df.columns for rc in remove_cols), "dataFrame is missing columns defined in remove_cols!"
    
    # Find daily average of all columns
    daily_avg = df.groupby(['id','slope_angle','slope_azi',pd.Grouper(key='date', freq='D')]).mean()

    avgs = daily_avg.reset_index()
    
    removed_cols = avgs[remove_cols]
    avgs = avgs.drop(columns=remove_cols)
    
    return avgs, removed_cols
    