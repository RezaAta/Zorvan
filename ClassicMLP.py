import numpy as np

class ClassicMLP:
    def __init__(self, input_size, output_size, hidden_layers, hidden_activation="sigmoid", output_activation="linear", learning_rate=0.001, initial_weight=None, use_bias=True):
        self.input_size = input_size
        self.output_size = output_size
        self.hidden_layers = hidden_layers
        self.hidden_activation = hidden_activation
        self.output_activation = output_activation
        self.learning_rate = learning_rate
        self.initial_weight = initial_weight
        self.use_bias = use_bias

        self.weights = self._initialize_weights()
        self.biases = self._initialize_biases()

    def _initialize_weights(self):
        layer_dims = [self.input_size] + self.hidden_layers + [self.output_size]
        if self.initial_weight is not None:
            return [np.full((layer_dims[i], layer_dims[i + 1]), self.initial_weight) for i in range(len(layer_dims) - 1)]
        return [np.random.uniform(-1, 1, (layer_dims[i], layer_dims[i + 1])) for i in range(len(layer_dims) - 1)]

    def _initialize_biases(self):
        layer_dims = [self.input_size] + self.hidden_layers + [self.output_size]
        return [np.zeros((1, layer_dims[i + 1])) for i in range(len(layer_dims) - 1)] if self.use_bias else [None] * (len(layer_dims) - 1)

    def _activation(self, x, activation_type):
        if activation_type == "sigmoid":
            return 1 / (1 + np.exp(-x))
        if activation_type == "relu":
            return np.maximum(0, x)
        if activation_type == "linear":
            return x
        raise ValueError("Unsupported activation function.")

    def _activation_derivative(self, x, activation_type):
        if activation_type == "sigmoid":
            return x * (1 - x)
        if activation_type == "relu":
            return np.where(x > 0, 1, 0)
        if activation_type == "linear":
            return np.ones_like(x)
        raise ValueError("Unsupported activation function.")

    def forward_pass(self, X):
        activations = [X]
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            z = np.dot(activations[-1], w)
            if self.use_bias:
                z += b
            activation_type = self.hidden_activation if i < len(self.hidden_layers) else self.output_activation
            a = self._activation(z, activation_type)
            activations.append(a)
        return activations

    def backward_pass(self, X, y, activations):
        errors = [activations[-1] - y]
        deltas = [errors[-1] * self._activation_derivative(activations[-1], self.output_activation)]

        for i in range(len(self.weights) - 2, -1, -1):
            error = np.dot(deltas[-1], self.weights[i + 1].T)
            delta = error * self._activation_derivative(activations[i + 1], self.hidden_activation)
            deltas.append(delta)

        deltas.reverse()

        for i in range(len(self.weights)):
            self.weights[i] -= self.learning_rate * np.dot(activations[i].T, deltas[i])
            if self.use_bias:
                self.biases[i] -= self.learning_rate * np.sum(deltas[i], axis=0, keepdims=True)

    def train(self, X, y, epochs=100, batch_size=32):
        mse_history = []
        for epoch in range(epochs):
            mse = 0
            for i in range(0, X.shape[0], batch_size):
                X_batch = X[i:i + batch_size]
                y_batch = y[i:i + batch_size]

                activations = self.forward_pass(X_batch)
                self.backward_pass(X_batch, y_batch, activations)

                mse += np.mean((activations[-1] - y_batch) ** 2)

            mse /= (X.shape[0] / batch_size)
            mse_history.append(mse)
            print(f"Epoch {epoch + 1}/{epochs}, MSE: {mse:.4f}")

        return mse_history

    def predict(self, X):
        activations = self.forward_pass(X)
        return activations[-1]

    def evaluate(self, X, y):
        predictions = self.predict(X)
        mae = np.mean(np.abs(predictions - y))
        return mae
