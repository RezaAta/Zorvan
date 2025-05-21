from ClassicMLP import ClassicMLP
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np

# Load Diabetes Dataset
data = load_diabetes()
X = data.data
y = data.target.reshape(-1, 1)

# Detect and remove outliers using IQR
q1 = np.percentile(y, 25, axis=0)  # First quartile
q3 = np.percentile(y, 75, axis=0)  # Third quartile
iqr = q3 - q1  # Interquartile range
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

# Mask for filtering non-outliers
non_outlier_mask = (y >= lower_bound) & (y <= upper_bound)
X = X[non_outlier_mask.flatten()]
y = y[non_outlier_mask.flatten()]

# Split and scale the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler_X = StandardScaler()
X_train = scaler_X.fit_transform(X_train)
X_test = scaler_X.transform(X_test)


# Initialize and train the model
mlp = ClassicMLP(
    input_size=X_train.shape[1],
    output_size=1,
    hidden_layers=[8, 4, 2],
    hidden_activation="sigmoid",
    output_activation="linear",
    learning_rate=0.00001,
    use_bias=False
)
mse_history = mlp.train(X_train, y_train, epochs=500, batch_size=1)

# Evaluate the model
mae = mlp.evaluate(X_test, y_test)
print(f"Test MAE: {mae:.4f}")

# Plot training loss
plt.plot(mse_history, label='Training Loss (MSE)')
plt.title('Training Loss Curve')
plt.xlabel('Epochs')
plt.ylabel('Loss (MSE)')
plt.legend()
plt.show()
