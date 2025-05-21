from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
import numpy as np
import matplotlib.pyplot as plt
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode

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
X_train, X_test, y_train, y_test = train_test_split(X, y_onehot, test_size=0.2, random_state=42)

# Step 2: Build the MLP graph
mlpGraph = MLPGraph(numInputs=4, numOutputs=3, numHiddenLayers=2, hiddenLayerSizes=[6, 4],activationFunction = SigmoidNode)
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
networkLength = 3 * (len(mlpGraph.hiddenLayers)+1)
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

# Step 5: Evaluate the network
# Use the MLP graph for predictions
mlp_processor = GraphProcessor(mlpGraph, max_workers=16, verbose=False)
mlpGraph.LoadData(X_test.T.tolist(), y_test.T.tolist())  # Load test data into the graph
mlp_processor.ComputeGraph(networkLength)  # Warm up for valid values

# Gather predictions
predictions = []
actuals = []
for i in range(len(X_test)):
    mlp_processor.ComputeGraph(1)
    prediction = [outputNode.value for _, outputNode in mlpGraph.outputLayer]
    predictions.append(prediction)
    actuals.append(y_test[i])

# Convert predictions and actuals for metric calculation
predicted_classes = np.argmax(predictions, axis=1)
actual_classes = np.argmax(actuals, axis=1)

# Compute metrics
from sklearn.metrics import precision_score, recall_score, f1_score
precision = precision_score(actual_classes, predicted_classes, average="weighted")
recall = recall_score(actual_classes, predicted_classes, average="weighted")
f1 = f1_score(actual_classes, predicted_classes, average="weighted")

print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1 Score: {f1:.4f}")
