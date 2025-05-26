from ComputationalGraphs.Core.DrawioIO import DrawioIO
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode



def FibonacciTest():
    graph = Graph()

    fib1 = DisplayNode(name="Fibonacci n-1", value=1)
    fibn = AdditionNode(name="Fibonacci n", value=1)

    graph.AddNode(fib1, fibn)

    graph.ConnectPreNode(fibn, fibn, fib1)
    graph.ConnectPreNode(fib1, fibn)

# Initialize processor with parallel execution
    processor = GraphProcessor(graph, max_workers=4)
    processor.ComputeGraph(iterations=10)

    DrawioIO.save(graph,"new graph.drawio")


    loadedGraph = DrawioIO.load("new graph.drawio")

    processor.graph = loadedGraph
    processor.ComputeGraphSingleThread(3)


def CustsomGraphLoadTest():
    loadedGraph = DrawioIO.load("new graph.drawio")

    processor = GraphProcessor(loadedGraph, max_workers=4)
    processor.ComputeGraph(iterations=10)


def GeneratedMLPTestOnDiabetes():
    from ComputationalGraphs.Core.MLPGraph import MLPGraph
    from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
    from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
    import numpy as np
    from sklearn.datasets import load_diabetes
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

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
        activationFunction=SigmoidNode  # Use ReLU activation for hidden layers
    )
    mlpGraph.BuildMLP()

    backprop_graph = BackpropGraph(mlpGraph, learningRate=0.00001)
    backprop_graph.BuildBackprop()

    # Combine MLP and Backpropagation graphs into a complete graph
    fullMLPGraph = Graph()
    for node in mlpGraph.nodes:
        fullMLPGraph.AddNode(node)
    for node in backprop_graph.nodes:
        fullMLPGraph.AddNode(node)

    # Update adjacency matrix
    mlpGraph.UpdateAdjacencyMatrix()

    DrawioIO.save(fullMLPGraph,"FullMLPGraph.drawio")
    DrawioIO.save(backprop_graph,"BackpropGraph.drawio")
    DrawioIO.save(mlpGraph,"MLPGraph.drawio")

def GeneratedMLPTestOnXOR():
    from ComputationalGraphs.Core.MLPGraph import MLPGraph
    from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
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

    DrawioIO.save(fullMLPGraph,"FullMLPGraph.drawio")
    DrawioIO.save(backprop_graph,"BackpropGraph.drawio")
    DrawioIO.save(mlpGraph,"MLPGraph.drawio")

FibonacciTest()
#CustsomGraphLoadTest()
#GeneratedMLPTestOnDiabetes()
#GeneratedMLPTestOnXOR()
#DrawioIO.generate_template_graph("Template.drawio")
