from MLPGraph import MLPGraph
from BackpropGraph import BackpropGraph
from GraphProcessor import GraphProcessor
import matplotlib.pyplot as plt



testMLPGraph = MLPGraph(1,1,1,hiddenLayerSizes=[1])

testMLPGraph.BuildMLP()

testMLPGraph.LoadData([[0.9, 1]],[[0.9, 1]])

testBackPropGraph = BackpropGraph(testMLPGraph, learningRate = 0.1)
testBackPropGraph.BuildBackprop()

mlpProcessor = GraphProcessor(testMLPGraph,max_workers=16, verbose= False)

forwardPassLength = 3 * (len(testMLPGraph.hiddenLayers)+1)

mlpProcessor.ComputeGraph(forwardPassLength)

for node in testBackPropGraph.nodes:
    testMLPGraph.AddNode(node)

epochs = 100 * forwardPassLength

accuracy_or_error_values = []

testMLPGraph.UpdateAdjacencyMatrix()

for epoch in range(epochs):
    # Forward pass (e.g., 10 iterations)
    mlpProcessor.ComputeGraph(1)
    # testMLPGraph.DisplayGraph()

    # Calculate accuracy or error and record it
    # Let's assume Mean Squared Error for simplicity
    total_error = sum(node.value*node.value for node in testMLPGraph.errorLayer) / len(testMLPGraph.errorLayer)
    accuracy_or_error_values.append(total_error)  # Append total error for this epoch

    # Backpropagation pass (1 iteration)
    #backpropProcessor.ComputeGraph(1)

    # # Reset error nodes for the next epoch
    # for node in mlp_graph.errorLayer:
    #     node.value = None


# Plotting the results
plt.plot(range(epochs), accuracy_or_error_values, label='Mean Squared Error')
plt.xlabel('Epochs')
plt.ylabel('Error')
plt.title('Error Change Over Epochs')
plt.legend()
plt.show()

#backprop_graph.DisplayGraph()
# testMLPGraph.DisplayGraph()
