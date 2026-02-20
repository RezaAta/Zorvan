# Moved from zorvan/Tests/MLPTests/TestingOnHousePricePrediction.py
# Renamed to Experiments/exp_testing_on_house_price.py

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.ReLUNode import ReLUNode
from zorvan.Nodes.SigmoidNode import SigmoidNode

# Load housing dataset
data = fetch_california_housing()
inputData = data.data
targetData = data.target

# Detect and remove outliers using IQR
q1 = np.percentile(targetData, 25, axis=0)
q3 = np.percentile(targetData, 75, axis=0)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

non_outlier_mask = (targetData >= lower_bound) & (targetData <= upper_bound)
inputData = inputData[non_outlier_mask.flatten()]
targetData = targetData[non_outlier_mask.flatten()]

targetData = targetData.reshape(-1, 1)

# Split and scale
X_train, X_test, y_train, y_test = train_test_split(
    inputData, targetData, test_size=0.2, random_state=42
)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Reshape data for MLPGraph
y_train = y_train.T.tolist()
y_test = y_test.T.tolist()
X_train = X_train.T.tolist()
X_test = X_test.T.tolist()

# Initialize and build MLPGraph
mlpGraph = MLPGraph(
    numInputs=len(X_train),
    numOutputs=1,
    numHiddenLayers=3,
    hiddenLayerSizes=[8, 4, 2],
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,
)
mlpGraph.BuildMLP()

backprop_graph = BackpropGraph(mlpGraph, learningRate=0.00001)
backprop_graph.BuildBackprop()

# Combine and update
fullMLPGraph = Graph()
for node in mlpGraph.nodes:
    fullMLPGraph.AddNode(node)
for node in backprop_graph.nodes:
    fullMLPGraph.AddNode(node)

mlpGraph.UpdateAdjacencyMatrix()

mlpProcessor = GraphProcessor(mlpGraph, max_workers=32, verbose=False)
fullGraphProcessor = GraphProcessor(fullMLPGraph, max_workers=32, verbose=False)

# Training setup
networkLength = 3 * (len(mlpGraph.hiddenLayers) + 1)
mlpProcessor.ComputeGraphSingleThread(networkLength)

fakeBatchSize = 1
epochs = 50
numberOfIterationsInEpochs = len(X_train[0])
totalIterations = epochs * numberOfIterationsInEpochs * fakeBatchSize

mlpGraph.CreateErrorBuffers(totalIterations, mse_buffer_size=numberOfIterationsInEpochs)
errorBuffers = mlpGraph.errorBuffers
for eb in errorBuffers:
    if eb not in fullMLPGraph.nodes:
        fullMLPGraph.AddNode(eb)
if hasattr(mlpGraph, "mseNodes"):
    for mse in mlpGraph.mseNodes:
        if mse not in fullMLPGraph.nodes:
            fullMLPGraph.AddNode(mse)

fullGraphProcessor.ComputeGraphSingleThread(totalIterations + networkLength + 1)

# Compute MSE over epochs and plot
MSEOverEpochs = []
for i in range(totalIterations):
    mse = 0
    for errorBuffer in errorBuffers:
        mse += (errorBuffer.buffer[i]) ** 2
    mse = mse / len(errorBuffers)
    MSEOverEpochs.append(mse)

MSEOverEpochs = np.array(MSEOverEpochs)
newMSEOverEpochs = MSEOverEpochs.reshape(-1, fakeBatchSize * numberOfIterationsInEpochs)
newMSEOverEpochs = np.mean(newMSEOverEpochs, axis=1)

plt.plot(range(len(newMSEOverEpochs)), newMSEOverEpochs, label="Mean Squared Error")
plt.xlabel("Epochs")
plt.ylabel("Error")
plt.title("Error Change Over Epochs (House Price Prediction)")
plt.legend()
plt.show()

# Testing phase
mlpGraph.PrepareForTest(X_test, y_test)
mlpProcessor.ComputeGraphSingleThread(len(X_test[0]) + networkLength)

predictionValues = []
for predictionBuffer in mlpGraph.predictionBuffers:
    predictionValues.extend(predictionBuffer.buffer)

predictionValues = np.array(predictionValues)
mae = np.mean(np.abs(np.array(y_test).flatten() - predictionValues.flatten()))
print(f"Mean Absolute Error on Test Set: {mae:.4f}")
