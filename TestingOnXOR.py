
from MLPGraph import MLPGraph
from Graph import Graph
from BackpropGraph import BackpropGraph
from GraphProcessor import GraphProcessor
import matplotlib.pyplot as plt
from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np
import matplotlib.pyplot as plt
from BufferNode import BufferNode
from ReLUNode import ReLUNode
from SigmoidNode import SigmoidNode

if __name__ == '__main__':

    # Initialize MLP Graph and Backpropagation Graph
    mlpGraph = MLPGraph(numInputs=2, numOutputs=1, numHiddenLayers=1, hiddenLayerSizes=[2], activationFunction = SigmoidNode, outputLayerType= SigmoidNode)
    mlpGraph.BuildMLP()

    backprop_graph = BackpropGraph(mlpGraph, learningRate = 0.25)
    backprop_graph.BuildBackprop()

    # XOR Dataset
    X = [[1, 1, 0, 0], [1, 0, 1, 0]]  # Inputs (columns are data points)
    y = [[0, 1, 1, 0]]                # Labels

    mlpGraph.LoadData(X, y)

    # Combine MLP and Backpropagation graphs into a complete graph
    fullMLPGraph = Graph()
    for node in mlpGraph.nodes:
        fullMLPGraph.AddNode(node)
    for node in backprop_graph.nodes:
        fullMLPGraph.AddNode(node)  

    # Update adjacency matrix
    mlpGraph.UpdateAdjacencyMatrix()

    # Initialize Graph Processors
    mlpProcessor = GraphProcessor(mlpGraph, max_workers=16, verbose=False)
    fullGraphProcessor = GraphProcessor(fullMLPGraph, max_workers=16, verbose=False)

    # Network warmup
    networkLength = 3 * (len(mlpGraph.hiddenLayers) + 1)
    mlpProcessor.ComputeGraph(networkLength)

    fakeBatchSize = 4
    # Training
    epochs = 10 * fakeBatchSize # must be multiplied by batchsize if we want to know the real values
    MSEOverEpochs = []
    mlpGraph.CreateErrorBuffers(epochs)
    errorBuffers = mlpGraph.errorBuffers
    fullMLPGraph.AddNode(*errorBuffers)

    fullGraphProcessor.ComputeGraph(epochs + networkLength + 1)

    #Calculate the mseOverEpochs
    for i in range(epochs):
        mse = 0
        for errorBuffer in errorBuffers:
            mse += (errorBuffer.buffer[i])**2
        mse = mse/len(errorBuffers)
        MSEOverEpochs.append(mse)


    MSEOverEpochs = np.array(MSEOverEpochs)
    newMSEOverEpochs = MSEOverEpochs.reshape(-1,4)
    newMSEOverEpochs = np.mean(newMSEOverEpochs, axis=1)

    mlpGraph.PrepareForTest(X, y)
    predictionBuffers = mlpGraph.predictionBuffers

    testingEpochs = len(X[0]) + networkLength + 1 # extra epochs to flush forward the network
    mlpProcessor.ComputeGraph(testingEpochs)  # Run forward pass for each input

    # Predictions
    predictions = []
    for predictionBuffer in predictionBuffers:
        predictions.append(predictionBuffer.buffer)
    ground_truth = np.array(y).flatten()


    # Threshold predictions
    threshold = 0.5
    predictions_binary = [1 if pred > threshold else 0 for pred in predictions[0]]

    # Calculate Precision, Recall, and F1 Score
    precision = precision_score(ground_truth, predictions_binary)
    recall = recall_score(ground_truth, predictions_binary)
    f1 = f1_score(ground_truth, predictions_binary)

    # Results
    print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1 Score: {f1:.4f}")

    # Plotting Error Over Epochs
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
