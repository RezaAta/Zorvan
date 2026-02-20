# Moved from zorvan/Tests/MLPTests/TestingOnIris.py
# Renamed to Experiments/exp_testing_on_iris.py

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.SigmoidNode import SigmoidNode

# Step 1: Load and preprocess the Iris dataset
iris = load_iris()
X = iris.data
y = iris.target

# Normalize features
scaler = MinMaxScaler()
X = scaler.fit_transform(X)

# One-hot encode labels
encoder = OneHotEncoder(sparse_output=False)
y_onehot = encoder.fit_transform(y.reshape(-1, 1))

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_onehot, test_size=0.2, random_state=42
)

# Step 2: Build the MLP graph
mlpGraph = MLPGraph(
    numInputs=4,
    numOutputs=3,
    numHiddenLayers=2,
    hiddenLayerSizes=[6, 4],
    activationFunction=SigmoidNode,
)
mlpGraph.BuildMLP()

# Initialize random weights for the MLP
for layer in mlpGraph.weightLayers:
    for row in layer:
        for weightNode in row:
            weightNode.value = np.random.uniform(-0.5, 0.5)

# Load the training data into the MLP graph
mlpGraph.LoadData(X_train.T.tolist(), y_train.T.tolist())

# Step 3: Build the Backpropagation graph
backpropGraph = BackpropGraph(mlpGraph, learningRate=0.05)
backpropGraph.BuildBackprop()

# Combine MLP and Backprop graphs
fullMLPGraph = Graph()
for node in mlpGraph.nodes:
    fullMLPGraph.AddNode(node)
for node in backpropGraph.nodes:
    fullMLPGraph.AddNode(node)
fullMLPGraph.UpdateAdjacencyMatrix()

# Step 4: Train the network
fullGraphProcessor = GraphProcessor(fullMLPGraph, max_workers=16, verbose=False)

# Warm up the network to ensure valid values
networkLength = 3 * (len(mlpGraph.hiddenLayers) + 1)
fullGraphProcessor.ComputeGraph(networkLength)

epochs = 100 * networkLength
mse_values = []

for epoch in range(epochs):
    fullGraphProcessor.ComputeGraph(1)

    # Compute Mean Squared Error
    mse = sum(node.value**2 for node in mlpGraph.errorLayer) / len(mlpGraph.errorLayer)
    mse_values.append(mse)

# Plot MSE over epochs
plt.plot(range(epochs), mse_values, label="Mean Squared Error")
plt.title("Error Over Epochs (Iris - MLP Graph)")
plt.xlabel("Epoch")
plt.ylabel("MSE")
plt.legend()
plt.show()
