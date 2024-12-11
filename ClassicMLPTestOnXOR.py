import numpy as np
import matplotlib.pyplot as plt

# Sigmoid Activation Function
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# Derivative of Sigmoid
def sigmoid_derivative(x):
    return x * (1 - x)

class ClassicMLP:
    def __init__(self, learning_rate=0.05):
        self.learning_rate = learning_rate
        
        # Initialize weights
        self.weights_input_hidden = np.ones((2, 2))  # 2 inputs -> 2 hidden neurons
        self.weights_hidden_output = np.ones((2, 1))  # 2 hidden neurons -> 1 output
        
        # No biases (b = 0)
        self.bias_hidden = np.zeros((2,))
        self.bias_output = np.zeros((1,))

    def forward(self, X):
        """
        Perform the forward pass.
        """
        # Hidden layer: Inputs to hidden layer
        self.hidden_input = np.dot(X, self.weights_input_hidden) + self.bias_hidden
        self.hidden_output = sigmoid(self.hidden_input)
        
        # Output layer: Hidden to output layer
        self.output_input = np.dot(self.hidden_output, self.weights_hidden_output) + self.bias_output
        self.output = sigmoid(self.output_input)
        
        return self.output

    def backward(self, X, y):
        """
        Perform the backward pass and update weights.
        """
        # Output layer error
        error_output = y - self.output
        delta_output = error_output * sigmoid_derivative(self.output)
        
        # Hidden layer error
        error_hidden = delta_output.dot(self.weights_hidden_output.T)
        delta_hidden = error_hidden * sigmoid_derivative(self.hidden_output)
        
        # Update weights and biases
        self.weights_hidden_output += self.learning_rate * self.hidden_output.T.dot(delta_output)
        self.weights_input_hidden += self.learning_rate * X.T.dot(delta_hidden)

    def train(self, X, y, epochs=1000):
        """
        Train the MLP on the dataset.
        """
        errors = []
        for epoch in range(epochs):
            for xi, yi in zip(X, y):
                xi = xi.reshape(1, -1)  # Ensure input is 2D
                yi = yi.reshape(1, -1)
                
                self.forward(xi)
                self.backward(xi, yi)
            
            # Calculate MSE for the epoch
            mse = np.mean((y - self.forward(X))**2)
            errors.append(mse)
        
        return errors

    def compute_f1(self, X, y, threshold=0.5):
        """
        Compute precision, recall, and F1 score.
        """
        predictions = (self.forward(X) > threshold).astype(int)  # Threshold outputs
        tp = np.sum((predictions == 1) & (y == 1))  # True positives
        fp = np.sum((predictions == 1) & (y == 0))  # False positives
        fn = np.sum((predictions == 0) & (y == 1))  # False negatives
        
        # Precision, Recall, and F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return precision, recall, f1


# XOR Dataset
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([[0], [1], [1], [0]])

# Create and train the MLP
mlp = ClassicMLP(learning_rate=1)
errors = mlp.train(X, y, epochs=100)

# Plot the error over epochs
plt.plot(range(len(errors)), errors)
plt.title("Error over Epochs for XOR (Classic MLP)")
plt.xlabel("Epoch")
plt.ylabel("Mean Squared Error")
plt.show()

# Evaluate the F1 metric
precision, recall, f1 = mlp.compute_f1(X, y)
print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1 Score: {f1:.4f}")

# Test the MLP
print("\nTesting MLP Predictions:")
for xi, yi in zip(X, y):
    output = mlp.forward(xi)
    print(f"Input: {xi}, Predicted: {output[0]:.4f}, Actual: {yi[0]}")
