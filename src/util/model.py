import numpy as np

from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, root_mean_squared_error, mean_absolute_error, mean_squared_error

def eval_model(y_a, y_p, plot=False, norm = False):
    acc = accuracy_score(y_a, y_p)
    print(f"Accuracy {acc:.2f}")
    print(f"MSE: {mean_squared_error(y_a, y_p)}")
    print(f"RMSE: {root_mean_squared_error(y_a, y_p)}")
    print(f"MAE: {mean_absolute_error(y_a, y_p)}")

    if plot:
        labels = np.unique(y_a)

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