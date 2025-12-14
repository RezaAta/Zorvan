import numpy as np


class ClassicMLP:
    def __init__(
        self,
        input_size,
        output_size,
        hidden_layers=None,
        num_hidden_layers=1,
        hidden_activation="sigmoid",
        output_activation="linear",
        learning_rate=0.001,
        initial_weight=None,
        use_bias=False,
    ):
        """
        Initialize Classic MLP with flexible hidden layer architecture.

        Args:
            input_size: Number of input features
            output_size: Number of output neurons
            hidden_layers: List specifying neurons per hidden layer (e.g., [10, 5, 3])
                          If None, will create num_hidden_layers with input_size neurons each
            num_hidden_layers: Number of hidden layers (only used if hidden_layers=None)
            hidden_activation: Activation function for hidden layers ("sigmoid", "relu", "linear", "tanh") - may be a string or a list per-hidden-layer (for mixed activations)
            output_activation: Activation function for output layer
            learning_rate: Learning rate for gradient descent
            initial_weight: If specified, initialize all weights to this value (for testing)
            use_bias: Whether to use bias terms
        """
        self.input_size = input_size
        self.output_size = output_size
        # Support both old API (hidden_layers as list) and new flexible API
        if hidden_layers is not None:
            self.hidden_layers = (
                hidden_layers
                if isinstance(hidden_layers, list)
                else [hidden_layers] * num_hidden_layers
            )
        else:
            self.hidden_layers = [input_size] * num_hidden_layers
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
            return [
                np.full((layer_dims[i], layer_dims[i + 1]), self.initial_weight)
                for i in range(len(layer_dims) - 1)
            ]
        return [
            np.random.uniform(-1, 1, (layer_dims[i], layer_dims[i + 1]))
            for i in range(len(layer_dims) - 1)
        ]

    def _initialize_biases(self):
        layer_dims = [self.input_size] + self.hidden_layers + [self.output_size]
        return (
            [np.zeros((1, layer_dims[i + 1])) for i in range(len(layer_dims) - 1)]
            if self.use_bias
            else [None] * (len(layer_dims) - 1)
        )

    def _activation(self, x, activation_type):
        if activation_type == "sigmoid":
            return 1 / (1 + np.exp(-x))
        if activation_type == "relu":
            return np.maximum(0, x)
        if activation_type == "linear":
            return x
        if activation_type == "tanh":
            return np.tanh(x)
        raise ValueError("Unsupported activation function.")

    def _activation_derivative(self, x, activation_type):
        if activation_type == "sigmoid":
            return x * (1 - x)
        if activation_type == "relu":
            return np.where(x > 0, 1, 0)
        if activation_type == "linear":
            return np.ones_like(x)
        if activation_type == "tanh":
            # x is tanh(x) (activation output), derivative = 1 - tanh(x)^2
            return 1 - (x**2)
        raise ValueError("Unsupported activation function.")

    def forward_pass(self, X):
        activations = [X]
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            z = np.dot(activations[-1], w)
            if self.use_bias:
                z += b
            if i < len(self.hidden_layers):
                activation_type = (
                    self.hidden_activation[i]
                    if isinstance(self.hidden_activation, (list, tuple))
                    else self.hidden_activation
                )
            else:
                activation_type = self.output_activation
            a = self._activation(z, activation_type)
            activations.append(a)
        return activations

    def backward_pass(self, X, y, activations):
        errors = [activations[-1] - y]
        deltas = [
            errors[-1]
            * self._activation_derivative(activations[-1], self.output_activation)
        ]

        for i in range(len(self.weights) - 2, -1, -1):
            error = np.dot(deltas[-1], self.weights[i + 1].T)
            # Determine activation type for this hidden layer (support list of activations)
            activation_type = (
                self.hidden_activation[i]
                if isinstance(self.hidden_activation, (list, tuple))
                else self.hidden_activation
            )
            delta = error * self._activation_derivative(
                activations[i + 1], activation_type
            )
            deltas.append(delta)

        deltas.reverse()

        for i in range(len(self.weights)):
            self.weights[i] -= self.learning_rate * np.dot(activations[i].T, deltas[i])
            if self.use_bias:
                self.biases[i] -= self.learning_rate * np.sum(
                    deltas[i], axis=0, keepdims=True
                )

    def train(self, X, y, epochs=100, batch_size=32):
        mse_history = []
        for epoch in range(epochs):
            mse = 0
            for i in range(0, X.shape[0], batch_size):
                X_batch = X[i : i + batch_size]
                y_batch = y[i : i + batch_size]

                activations = self.forward_pass(X_batch)
                self.backward_pass(X_batch, y_batch, activations)

                mse += np.mean((activations[-1] - y_batch) ** 2)

            mse /= X.shape[0] / batch_size
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

    def get_named_weights(self):
        """Return a mapping of weight names (concurrent MLP naming) to values.

        Naming conventions used:
        - Input -> first hidden: W_x{i}H0N{j}
        - Hidden -> Hidden: W_H{layer}N{i}H{layer+1}N{j}
        - Last Hidden -> Output: W_H{last}N{i}y{j}
        """
        named = {}
        layer_dims = [self.input_size] + self.hidden_layers + [self.output_size]
        for l in range(len(self.weights)):
            rows, cols = self.weights[l].shape
            for i in range(rows):
                for j in range(cols):
                    if l == 0:
                        # Input -> first hidden
                        key = f"W_x{i}H0N{j}"
                    elif l == len(self.weights) - 1:
                        # Last hidden -> output
                        key = f"W_H{l-1}N{i}y{j}"
                    else:
                        # Hidden -> Hidden
                        key = f"W_H{l-1}N{i}H{l}N{j}"
                    named[key] = self.weights[l][i, j]
        return named
