from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from ComputationalGraphs.Nodes.ReLUNode import ReLUNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
from sklearn.preprocessing import StandardScaler
import time

# Load Diabetes Dataset
data = load_diabetes()
inputData = data.data  # Features
targetData = data.target  # Target reshaped to 2D

# Detect and remove outliers using IQR
q1 = np.percentile(targetData, 25, axis=0)  # First quartile
q3 = np.percentile(targetData, 75, axis=0)  # Third quartile
iqr = q3 - q1  # Interquartile range
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

# Mask for filtering non-outliers
non_outlier_mask = (targetData >= lower_bound) & (targetData <= upper_bound)
inputData = inputData[non_outlier_mask.flatten()]
targetData = targetData[non_outlier_mask.flatten()]

targetData = targetData.reshape(-1, 1)

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(inputData, targetData, test_size=0.2, random_state=42)

# Scale the features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Reshape target data for compatibility with MLPGraph
# Transform y_train to a list of arrays, one for each output node
y_train = y_train.T.tolist()  # Shape: (1, n_samples)
y_test = y_test.T.tolist()    # Shape: (1, n_samples)
X_train = X_train.T.tolist()
X_test = X_test.T.tolist()

# Initialize MLP Graph and Backpropagation Graph
mlpGraph = MLPGraph(
    numInputs=len(X_train),
    numOutputs=1,
    numHiddenLayers=3,
    hiddenLayerSizes=[8, 4, 2],
    activationFunction=SigmoidNode  
)
mlpGraph.BuildMLP()

backprop_graph = BackpropGraph(mlpGraph, learningRate=0.00001)
backprop_graph.BuildBackprop()

# Load Training Data into the MLP
mlpGraph.LoadData(X_train, y_train)  # Inputs must also be transposed and converted to lists


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
mlpProcessor.ComputeGraphSingleThread(networkLength)

# Training
fakeBatchSize = 1
epochs = 500 
numberOfIterationsInEpochs = len(X_train[0])
totalIterations = epochs * numberOfIterationsInEpochs * fakeBatchSize
MSEOverEpochs = []
mlpGraph.CreateErrorBuffers(totalIterations)
errorBuffers = mlpGraph.errorBuffers
fullMLPGraph.AddNode(*errorBuffers)

print(f"\nTotal nodes: {len(fullMLPGraph.nodes)}")
print(f"Training iterations: {totalIterations + networkLength + 1}")
print("Starting training...\n")
start_time = time.time()
fullGraphProcessor.ComputeGraph(totalIterations + networkLength + 1)# +2 is for the error buffers
training_time = time.time() - start_time
print(f"Training completed in {training_time:.2f}s")
print(f"Iterations per second: {(totalIterations + networkLength + 1) / training_time:.0f}")

# Calculate the MSE over epochs
for i in range(totalIterations):
    mse = 0
    for errorBuffer in errorBuffers:
        mse += (errorBuffer.buffer[i])**2
    mse = mse / len(errorBuffers)
    MSEOverEpochs.append(mse)

MSEOverEpochs = np.array(MSEOverEpochs)
newMSEOverEpochs = MSEOverEpochs.reshape(-1, fakeBatchSize * numberOfIterationsInEpochs)
newMSEOverEpochs = np.mean(newMSEOverEpochs, axis=1)


# Plotting Error Over Epochs
plt.plot(range(len(newMSEOverEpochs)), newMSEOverEpochs, label="Mean Squared Error")
plt.xlabel("Epochs")
plt.ylabel("Error")
plt.title("Error Change Over Epochs (Diabetes Prediction)")
plt.legend()
plt.show()

# Testing phase
mlpGraph.PrepareForTest(X_test, y_test)  # Inputs must be transposed
predictionBuffers = mlpGraph.predictionBuffers

testingEpochs = len(X_test[0]) + networkLength # Extra epochs to flush forward the network
mlpProcessor.ComputeGraph(testingEpochs)

# Collect predictions
predictionValues = []
for predictionBuffer in predictionBuffers:
    predictionValues.extend(predictionBuffer.buffer)

# Convert to NumPy array and reshape
predictionValues = np.array(predictionValues)


# Calculate Mean Absolute Error (MAE)
mae = np.mean(np.abs(np.array(y_test).flatten() - predictionValues.flatten()))
print(f"Mean Absolute Error on Test Set: {mae:.4f}")
