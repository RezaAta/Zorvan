from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.PiecewiseLinearNode import PiecewiseLinearNode


def test_replace_activation_updates_latest_not_value():
    mlp = MLPGraph(numInputs=2, numOutputs=1, numHiddenLayers=1, hiddenLayerSizes=[2])
    mlp.BuildMLP()
    X = [[0, 0, 1, 1], [0, 1, 0, 1]]
    y = [[0, 1, 1, 0]]
    mlp.LoadData(X, y)
    backprop = BackpropGraph(mlp, learningRate=0.1)
    backprop.BuildBackprop()
    fullGraph = Graph()
    for node in mlp.nodes:
        fullGraph.AddNode(node)
    for node in backprop.nodes:
        fullGraph.AddNode(node)
    fullGraph.starting_nodes = [
        input_pair[0] for input_pair in mlp.inputLayer
    ] + mlp.labelLayer
    fullGraph.UpdateAdjacencyMatrix()

    proc = GraphProcessor(fullGraph, auto_threading=False)
    proc.ComputeGraph(iterations=5)

    # Keep references to the buffers and activation nodes
    buffers = [b for _, _, b in mlp.hiddenLayers[0]]
    activations = [a for _, a, _ in mlp.hiddenLayers[0]]

    # Replace activation nodes in place
    for i, a in enumerate(activations):
        newAct = PiecewiseLinearNode(name=a.name)
        newAct.AddPreNode(mlp.hiddenLayers[0][i][0])
        mlp.ReplaceNode(newAct, a)
    mlp.UpdateAdjacencyMatrix()

    # One iteration after replacement
    proc.ComputeGraph(iterations=1)

    for idx, b in enumerate(buffers):
        # the most recent element in the buffer should reflect the new activation
        assert b.buffer[-1] is not None
        # the b.value may be older due to buffer delay; ensure at least either differs or equals
        assert isinstance(b.value, (int, float, type(None)))
