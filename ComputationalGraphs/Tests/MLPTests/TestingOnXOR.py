
import time
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np
import matplotlib.pyplot as plt
from ComputationalGraphs.Nodes.ReLUNode import ReLUNode
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode


# Initialize MLP Graph and Backpropagation Graph
mlpGraph = MLPGraph(numInputs=2, 
                    numOutputs=1,
                    numHiddenLayers=1,
                    hiddenLayerSizes=[2],
                    activationFunction = SigmoidNode,
                    outputLayerType=SigmoidNode)
mlpGraph.BuildMLP()

backprop_graph = BackpropGraph(mlpGraph, learningRate = 0.01)
backprop_graph.BuildBackprop()


# XOR Dataset
X = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]  # Inputs (columns are data points)
y = [[0.0, 1.0, 1.0, 0.0]]                # Labels

mlpGraph.LoadData(X, y)

# Combine MLP and Backpropagation graphs into a complete graph
fullMLPGraph = Graph()
for node in mlpGraph.nodes:
    fullMLPGraph.AddNode(node)
for node in backprop_graph.nodes:
    fullMLPGraph.AddNode(node)  

# Update adjacency matrix
fullMLPGraph.UpdateAdjacencyMatrix()

# Initialize Graph Processors
mlpProcessor = GraphProcessor(mlpGraph, max_workers=1, verbose=False,visual=False)
fullGraphProcessor = GraphProcessor(fullMLPGraph, max_workers=1, verbose=False,visual=False)

# Network warmup
networkLength = 3 * (len(mlpGraph.hiddenLayers) + 1)
mlpProcessor.ComputeGraphSingleThread(networkLength)

# Training
fakeBatchSize = 1
epochs = 1000 #must be multiplied by batchsize if we want to know the real values
numberOfIterationsInEpochs = 4
totalIterations = epochs * numberOfIterationsInEpochs * fakeBatchSize
MSEOverEpochs = []
mlpGraph.CreateErrorBuffers(totalIterations)
errorBuffers = mlpGraph.errorBuffers
fullMLPGraph.AddNode(*errorBuffers)

start_time = time.time()
fullGraphProcessor.ComputeGraphSingleThread(totalIterations + 1)
end_time = time.time()


#Calculate the mseOverEpochs
for i in range(totalIterations):
    mse = 0
    for errorBuffer in errorBuffers:
        mse += (errorBuffer.buffer[i])**2
    mse = mse/len(errorBuffers)
    MSEOverEpochs.append(mse)


MSEOverEpochs = np.array(MSEOverEpochs)
newMSEOverEpochs = MSEOverEpochs.reshape(-1, numberOfIterationsInEpochs * fakeBatchSize)
newMSEOverEpochs = np.mean(newMSEOverEpochs, axis=1)

mlpGraph.PrepareForTest(X, y)
predictionBuffers = mlpGraph.predictionBuffers

testingEpochs = len(X[0]) + networkLength # extra epochs to flush forward the network
mlpProcessor.ComputeGraph(testingEpochs)  # Run forward pass for each input


# Predictions
predictions = []
for predictionBuffer in predictionBuffers:
    predictions.append(predictionBuffer.buffer)
ground_truth = np.array(y).flatten()

# Threshold predictions
threshold = 0.5
predictions_binary = [1 if pred > threshold else 0 for pred in predictions[0]]

#Calculate Precision, Recall, and F1 Score
precision = precision_score(ground_truth, predictions_binary)
recall = recall_score(ground_truth, predictions_binary)
f1 = f1_score(ground_truth, predictions_binary)

# Results
print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1 Score: {f1:.4f}")

#Plotting Error Over Epochs
plt.plot(range(len(newMSEOverEpochs)), newMSEOverEpochs, label='Mean Squared Error')
plt.xlabel('Epochs')
plt.ylabel('Error')
plt.title('Error Change Over Epochs (MLP + Backprop)')
plt.legend()
plt.show()

# Display Predictions
print("\nPredictions vs Ground Truth:")
for i in range(len(ground_truth)):
    print(f"Input: {X[0][i]}, {X[1][i]} -> Predicted: {predictions[0][i]:.4f} (Thresholded: {predictions_binary[i]}), Actual: {ground_truth[i]}")


# Calculate Mean Absolute Error (MAE)
mae = np.mean(np.abs(ground_truth - np.array(predictions).flatten()))
print(f"Mean Absolute Error on Test Set: {mae:.4f}")


trainingTime =  end_time - start_time
print(f"elapsed Time{trainingTime}")
