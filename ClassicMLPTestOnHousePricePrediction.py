import numpy as np
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from ClassicMLP import ClassicMLP

# Load California Housing Dataset
data = fetch_california_housing()
X = data.data
y = data.target.reshape(-1, 1)  # Ensure target is 2D

# Normalize features using MinMaxScaler (scaled to [0, 1])
scaler = MinMaxScaler()
X = scaler.fit_transform(X)

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
mlp = ClassicMLP(
    input_size=X_train.shape[1],
    output_size=1,
    hidden_layers=[8, 4, 2],
    hidden_activation="sigmoid",
    output_activation="linear",
    learning_rate=0.00001,
    use_bias=False
)
# Create and train the MLP
errors = mlp.train(X_train, y_train, epochs=100, batch_size=1)

# Evaluate the model
mae = mlp.evaluate(X_test, y_test)
print(f"Test MAE: {mae:.4f}")

# Plot the error over epochs
plt.plot(range(len(errors)), errors)
plt.title("Error over Epochs for California Housing (MLP with ReLU and Mini-Batching)")
plt.xlabel("Epoch")
plt.ylabel("Mean Squared Error")
plt.show()


