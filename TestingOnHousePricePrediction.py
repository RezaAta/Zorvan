from MLPGraph import MLPGraph
from BufferNode import BufferNode
from Graph import Graph
from BackpropGraph import BackpropGraph
from GraphProcessor import GraphProcessor
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from ReLUNode import ReLUNode

# Load California Housing Dataset
data = fetch_california_housing()
inputData = data.data.T  # Transpose to fit the column-based input expectation
targetData = data.target.reshape(1, -1)  # Target values as a single row


# Normalize features using MinMaxScaler
scaler = MinMaxScaler()
inputData = scaler.fit_transform(inputData)  # Scale features, keep the row-column structure
targetData = scaler.fit_transform(targetData)  # Normalize targets

# Split into train and test sets
train_size = int(0.8 * inputData.shape[1])
X_train, X_test = inputData[:, :train_size], inputData[:, train_size:]
y_train, y_test = targetData[:, :train_size], targetData[:, train_size:]

# Initialize MLP Graph and Backpropagation Graph
mlpGraph = MLPGraph(numInputs=X_train.shape[0], numOutputs=1, numHiddenLayers=3, hiddenLayerSizes=[16, 8, 4],activationFunction = ReLUNode)
mlpGraph.BuildMLP()

backprop_graph = BackpropGraph(mlpGraph, learningRate=0.01)
backprop_graph.BuildBackprop()

# Load Training Data into the MLP
mlpGraph.LoadData(X_train.tolist(), y_train.tolist())

# Combine MLP and Backpropagation graphs into a complete graph
fullMLPGraph = Graph()
for node in mlpGraph.nodes:
    fullMLPGraph.AddNode(node)
for node in backprop_graph.nodes:
    fullMLPGraph.AddNode(node)

# Update adjacency matrix
mlpGraph.UpdateAdjacencyMatrix()

# Initialize Graph Processors
mlpProcessor = GraphProcessor(mlpGraph, max_workers=32, verbose=False)
fullGraphProcessor = GraphProcessor(fullMLPGraph, max_workers=32, verbose=False)

# Network warmup
networkLength = 3 * (len(mlpGraph.hiddenLayers) + 1)
mlpProcessor.ComputeGraph(networkLength)


# Training
epochs = 100 #=X_train.shape[1]*5
MSEOverEpochs = []
mlpGraph.CreateErrorBuffers(epochs)
errorBuffers = mlpGraph.errorBuffers
fullMLPGraph.AddNode(*errorBuffers)

# Create a buffer node to keep all the errors of the training time

fullGraphProcessor.ComputeGraph(epochs + networkLength + 1)


#Calculate the mseOverEpochs
for i in range(epochs):
    mse = 0
    for errorBuffer in errorBuffers:
        mse += (errorBuffer.buffer[i])**2
    mse = mse/len(errorBuffers)
    MSEOverEpochs.append(mse)

# Plotting Error Over Epochs
plt.plot(range(epochs), MSEOverEpochs, label='Mean Squared Error')
plt.xlabel('Epochs')
plt.ylabel('Error')
plt.title('Error Change Over Epochs (California Housing Prediction)')
plt.legend()
plt.show()

mlpGraph.PrepareForTest(X_test.tolist(), y_test.tolist())
predictionBuffers = mlpGraph.predictionBuffers

testingEpochs = X_test.shape[1] + networkLength + 1 # extra epochs to flush forward the network
mlpProcessor.ComputeGraph(testingEpochs)  # Run forward pass for each input

predictionValues = []
for predictionBuffer in predictionBuffers:
    predictionValues.append(predictionBuffer.buffer)

# Rescale predictions back to the original scale
predictionsRescaled = np.array(predictionValues)#[:,::-1]
predictionsRescaled = scaler.inverse_transform(predictionsRescaled).reshape(-1, 1).flatten()
yTestRescaled = scaler.inverse_transform(y_test.T).flatten()

# Calculate Mean Absolute Error (MAE)
mae = np.mean(np.abs(yTestRescaled - predictionsRescaled))
print(f"Mean Absolute Error on Test Set: {mae:.4f}")


# # Display Predictions vs Ground Truth
# print("\nPredictions vs Ground Truth (Rescaled):")
# for i in range(len(yTestRescaled)):
#     print(f"Predicted: {predictionsRescaled[i]:.4f}, Actual: {yTestRescaled[i]:.4f}")
