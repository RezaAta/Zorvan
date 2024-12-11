import numpy as np
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

# Sigmoid Activation Function
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# Derivative of Sigmoid
def sigmoid_derivative(x):
    return x * (1 - x)

# ReLU Activation Function
def relu(x):
    return np.maximum(0, x)

# Derivative of ReLU
def relu_derivative(x):
    return np.where(x > 0, 1, 0)

# Xavier Initialization
def xavier_init(shape):
    return np.random.uniform(-np.sqrt(6 / sum(shape)), np.sqrt(6 / sum(shape)), shape)

# He Initialization
def he_init(shape):
    return np.random.randn(*shape) * np.sqrt(2 / shape[0])

class MLPRegressor:
    def __init__(self, input_size, hidden_sizes, output_size, learning_rate=0.01, activation="relu"):
        self.learning_rate = learning_rate
        self.activation_function = relu if activation == "relu" else sigmoid
        self.activation_derivative = relu_derivative if activation == "relu" else sigmoid_derivative
        
        # Initialize weights for each layer
        layer_sizes = [input_size] + hidden_sizes + [output_size]
        self.weights = [
            he_init((layer_sizes[i], layer_sizes[i + 1]))
            for i in range(len(layer_sizes) - 1)
        ]

    def forward(self, X):
        """Perform the forward pass."""
        self.layer_inputs = []
        self.layer_outputs = [X]  # Input is the output of the first layer
        
        for weight in self.weights[:-1]:  # Apply activation for all hidden layers
            input_to_layer = np.dot(self.layer_outputs[-1], weight)
            self.layer_inputs.append(input_to_layer)
            self.layer_outputs.append(self.activation_function(input_to_layer))
        
        # Output layer (linear activation for regression)
        final_input = np.dot(self.layer_outputs[-1], self.weights[-1])
        self.layer_inputs.append(final_input)
        self.output = final_input
        return self.output

    def backward(self, X, y):
        """Perform the backward pass and update weights."""
        # Output layer error and delta
        error = y - self.output
        delta = error  # No activation derivative for regression at output layer
        
        # Backpropagation through hidden layers
        deltas = [delta]
        for i in range(len(self.weights) - 2, -1, -1):  # Start from last hidden layer
            delta = np.dot(deltas[0], self.weights[i + 1].T) * self.activation_derivative(self.layer_inputs[i])
            deltas.insert(0, delta)
        
        # Update weights
        for i in range(len(self.weights)):
            self.weights[i] += self.learning_rate * np.dot(self.layer_outputs[i].T, deltas[i])

    def train(self, X, y, epochs=200, batch_size=32):
        """Train the MLP on the dataset using mini-batch gradient descent."""
        errors = []
        num_samples = X.shape[0]
        for epoch in range(epochs):
            # Shuffle data
            indices = np.arange(num_samples)
            np.random.shuffle(indices)
            X = X[indices]
            y = y[indices]
            
            # Process mini-batches
            batch_errors = []
            for start_idx in range(0, num_samples, batch_size):
                end_idx = start_idx + batch_size
                batch_X = X[start_idx:end_idx]
                batch_y = y[start_idx:end_idx]
                
                # Forward and backward pass for the batch
                self.forward(batch_X)
                self.backward(batch_X, batch_y)
                
                # Calculate batch MSE
                batch_mse = np.mean((batch_y - self.output)**2)
                batch_errors.append(batch_mse)
            
            # Average error for the epoch
            epoch_error = np.mean(batch_errors)
            errors.append(epoch_error)
        
        return errors

# Load California Housing Dataset
data = fetch_california_housing()
X = data.data
y = data.target.reshape(-1, 1)  # Ensure target is 2D

# Normalize features using MinMaxScaler (scaled to [0, 1])
scaler = MinMaxScaler()
X = scaler.fit_transform(X)

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create and train the MLP
mlp = MLPRegressor(input_size=8, hidden_sizes=[8, 4, 2], output_size=1, learning_rate=0.2, activation="relu")
errors = mlp.train(X_train, y_train, epochs=100, batch_size=1)

# Plot the error over epochs
plt.plot(range(len(errors)), errors)
plt.title("Error over Epochs for California Housing (MLP with ReLU and Mini-Batching)")
plt.xlabel("Epoch")
plt.ylabel("Mean Squared Error")
plt.show()

# Evaluate the model on the test set
predictions = mlp.forward(X_test)
mse = np.mean((y_test - predictions)**2)
print(f"Mean Squared Error on Test Set: {mse:.4f}")
