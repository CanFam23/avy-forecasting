import numpy as np

from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, root_mean_squared_error, mean_absolute_error, mean_squared_error

def eval_model(y_a, y_p, plot=False, norm = False):
    acc = accuracy_score(y_a, y_p)
    print(f"Accuracy {acc:.2f}")
    print(f"MSE: {mean_squared_error(y_a, y_p)}")
    print(f"RMSE: {root_mean_squared_error(y_a, y_p)}")
    print(f"MAE: {mean_absolute_error(y_a, y_p)}")

    if plot:
        if norm:
            cm = confusion_matrix(y_a, y_p, normalize="true")

            disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=np.unique(y_a))
            disp.plot(cmap='Blues', values_format='.2f')
        else:
            cm = confusion_matrix(y_a, y_p)

            disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=np.unique(y_a))
            disp.plot(cmap='Blues', values_format='d')