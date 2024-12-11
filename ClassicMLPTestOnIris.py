import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score
import matplotlib.pyplot as plt 

# Load the Iris dataset
iris = load_iris()
X = iris.data  # Features
y = iris.target.reshape(-1, 1)  # Labels as column vector

# Normalize features
scaler = StandardScaler()
X = scaler.fit_transform(X)

# One-hot encode target labels
encoder = OneHotEncoder(sparse_output=False)
y = encoder.fit_transform(y)

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# Sigmoid Activation Function
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# Derivative of Sigmoid
def sigmoid_derivative(x):
    return x * (1 - x)

class ClassicMLP:
    def __init__(self, input_size, hidden_sizes, output_size, learning_rate=0.01):
        self.learning_rate = learning_rate
        
        # Initialize weights
        self.weights_input_hidden = np.ones((input_size, hidden_sizes[0]))  # Input -> Hidden Layer 1
        self.weights_hidden_hidden = np.ones((hidden_sizes[0], hidden_sizes[1]))  # Hidden Layer 1 -> Hidden Layer 2
        self.weights_hidden_output = np.ones((hidden_sizes[1], output_size))  # Hidden Layer 2 -> Output
        
        # No biases (b = 0)

    def forward(self, X):
        """
        Perform the forward pass.
        """
        # Hidden Layer 1
        self.hidden1_input = np.dot(X, self.weights_input_hidden)
        self.hidden1_output = sigmoid(self.hidden1_input)
        
        # Hidden Layer 2
        self.hidden2_input = np.dot(self.hidden1_output, self.weights_hidden_hidden)
        self.hidden2_output = sigmoid(self.hidden2_input)
        
        # Output Layer
        self.output_input = np.dot(self.hidden2_output, self.weights_hidden_output)
        self.output = sigmoid(self.output_input)
        
        return self.output

    def backward(self, X, y):
        """
        Perform the backward pass and update weights.
        """
        # Output layer error and delta
        error_output = y - self.output
        delta_output = error_output * sigmoid_derivative(self.output)
        
        # Hidden Layer 2 error and delta
        error_hidden2 = np.dot(delta_output, self.weights_hidden_output.T)
        delta_hidden2 = error_hidden2 * sigmoid_derivative(self.hidden2_output)
        
        # Hidden Layer 1 error and delta
        error_hidden1 = np.dot(delta_hidden2, self.weights_hidden_hidden.T)
        delta_hidden1 = error_hidden1 * sigmoid_derivative(self.hidden1_output)
        
        # Update weights
        self.weights_hidden_output += self.learning_rate * np.dot(self.hidden2_output.T, delta_output)
        self.weights_hidden_hidden += self.learning_rate * np.dot(self.hidden1_output.T, delta_hidden2)
        self.weights_input_hidden += self.learning_rate * np.dot(X.T, delta_hidden1)

    def train(self, X, y, epochs=200):
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

    def compute_f1_multiclass(self, X, y):
        predictions = np.argmax(self.forward(X), axis=1)
        actuals = np.argmax(y, axis=1)
        print(f"Predicted Class Distribution: {np.bincount(predictions)}")
        print(f"Actual Class Distribution: {np.bincount(actuals)}")

        precision = precision_score(actuals, predictions, average="weighted", zero_division=0)
        recall = recall_score(actuals, predictions, average="weighted", zero_division=0)
        f1 = f1_score(actuals, predictions, average="weighted", zero_division=0)

        return precision, recall, f1
# Create and train the MLP
mlp = ClassicMLP(input_size=4, hidden_sizes=[6, 4], output_size=3, learning_rate=0.05)
errors = mlp.train(X_train, y_train, epochs=100)

# Plot the error over epochs
plt.plot(range(len(errors)), errors)
plt.title("Error over Epochs for Iris (Classic MLP)")
plt.xlabel("Epoch")
plt.ylabel("Mean Squared Error")
plt.show()

# Evaluate the F1 metric on the test set
precision, recall, f1 = mlp.compute_f1_multiclass(X_test, y_test)
print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1 Score: {f1:.4f}")
