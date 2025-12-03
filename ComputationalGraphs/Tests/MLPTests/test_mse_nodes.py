import pytest

from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode


def test_mse_nodes_concurrent():
    # Build small concurrent MLP for XOR
    mlp = MLPGraph(numInputs=2, numOutputs=1, numHiddenLayers=1, activationFunction=SigmoidNode, outputLayerType=LinearNode)
    mlp.BuildMLP()

    # Load XOR data (row-per-feature)
    X = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]
    y = [[0.0, 1.0, 1.0, 0.0]]
    mlp.LoadData(X, y)

    # Create error buffers and ensure MSE nodes added
    iterations = 10
    mlp.CreateErrorBuffers(iterations)
    assert hasattr(mlp, "mseNodes")
    assert len(mlp.mseNodes) == mlp.numOutputs
    # dataset size = len(X[0]) = 4
    for mse_node in mlp.mseNodes:
        assert mse_node.bufferSize == len(X[0])
        assert mse_node.mode == "continuous"
        # Check predecessor is error node
        assert len(mse_node.predecessors) == 1
        assert mse_node.predecessors[0].name.startswith("Error_y")


def test_mse_nodes_forward():
    # Build forward-processing MLP for XOR
    mlp = MLPGraphForwardProcessing(numInputs=2, numOutputs=1, numHiddenLayers=1, activationFunction=SigmoidNode, outputLayerType=LinearNode)
    mlp.BuildMLP()

    # Load XOR data (row-per-sample)
    X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
    y = [[0.0], [1.0], [1.0], [0.0]]
    mlp.LoadData(X, y)

    iterations = 10
    mlp.CreateErrorBuffers(iterations, allowNone=True)
    assert hasattr(mlp, "mseNodes")
    assert len(mlp.mseNodes) == mlp.numOutputs
    # dataset size = len(X) = 4
    for mse_node in mlp.mseNodes:
        assert mse_node.bufferSize == len(X)
        assert mse_node.mode == "continuous"
        # Check predecessor is error node
        assert len(mse_node.predecessors) == 1
        assert mse_node.predecessors[0].name.startswith("Error_y")


def test_mse_nodes_no_duplicates_concurrent():
    # Build small concurrent MLP and call CreateErrorBuffers twice
    mlp = MLPGraph(numInputs=2, numOutputs=1, numHiddenLayers=1, activationFunction=SigmoidNode, outputLayerType=LinearNode)
    mlp.BuildMLP()
    X = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]
    y = [[0.0, 1.0, 1.0, 0.0]]
    mlp.LoadData(X, y)
    iterations = 10

    # First call
    mlp.CreateErrorBuffers(iterations)
    first_count = len([n for n in mlp.nodes if n.__class__.__name__ == 'MeanSquaredErrorNode'])

    # Second call - should not increase number of MSE nodes
    mlp.CreateErrorBuffers(iterations)
    second_count = len([n for n in mlp.nodes if n.__class__.__name__ == 'MeanSquaredErrorNode'])

    assert first_count == mlp.numOutputs
    assert second_count == first_count


def test_mse_nodes_no_duplicates_forward():
    # Build small forward MLP and call CreateErrorBuffers twice
    mlp = MLPGraphForwardProcessing(numInputs=2, numOutputs=1, numHiddenLayers=1, activationFunction=SigmoidNode, outputLayerType=LinearNode)
    mlp.BuildMLP()
    X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
    y = [[0.0], [1.0], [1.0], [0.0]]
    mlp.LoadData(X, y)
    iterations = 10

    mlp.CreateErrorBuffers(iterations, allowNone=True)
    first_count = len([n for n in mlp.nodes if n.__class__.__name__ == 'MeanSquaredErrorNode'])

    mlp.CreateErrorBuffers(iterations, allowNone=True)
    second_count = len([n for n in mlp.nodes if n.__class__.__name__ == 'MeanSquaredErrorNode'])

    assert first_count == mlp.numOutputs
    assert second_count == first_count

    def test_examples_loader_no_duplicate_mse_nodes():
        # Ensure GUI loader's builders do not create duplicate MSE nodes in the combined graph
        from ComputationalGraphs.GUI.examples_loader import ExamplesLoader

        loader = ExamplesLoader()
        # We'll test a handful of builders that produce full graphs
        builders = [
            loader._build_simple_mlp_concurrent,
            loader._build_iris_mlp_concurrent,
            loader._build_simple_mlp,
        ]
        for b in builders:
            try:
                g = b()
            except Exception:
                # If builder fails due to environment, skip it
                continue
            mse_nodes = [n.name for n in g.nodes if n.__class__.__name__ == 'MeanSquaredErrorNode']
            # No duplicate names
            assert len(mse_nodes) == len(set(mse_nodes))


    def test_add_mse_to_full_graph_no_duplicates():
        # Simulate the example builder pattern: add mlp nodes, then create error buffers, then add error buffers/mse nodes
        from ComputationalGraphs.Core.Graph import Graph
        from ComputationalGraphs.Core.BackpropGraph import BackpropGraph

        # Build mlp and backprop
        mlp = MLPGraph(numInputs=3, numOutputs=2, numHiddenLayers=1, activationFunction=SigmoidNode, outputLayerType=LinearNode)
        mlp.BuildMLP()
        backprop = BackpropGraph(mlpGraph=mlp, learningRate=0.01)
        backprop.BuildBackprop()

        # Create full graph and add mlp/backprop nodes first
        fullGraph = Graph()
        for node in mlp.nodes:
            fullGraph.AddNode(node)
        for node in backprop.nodes:
            fullGraph.AddNode(node)

        # Create error buffers (added to mlp.nodes) and attempt to re-add to fullGraph
        mlp.CreateErrorBuffers(bufferSize=10, mse_buffer_size=5)
        for eb in mlp.errorBuffers:
            if eb not in fullGraph.nodes:
                fullGraph.AddNode(eb)
        for mse in mlp.mseNodes:
            if mse not in fullGraph.nodes:
                fullGraph.AddNode(mse)

        # Count MeanSquaredErrorNodes in full graph
        mse_in_graph = [n for n in fullGraph.nodes if n.__class__.__name__ == 'MeanSquaredErrorNode']
        assert len(mse_in_graph) == mlp.numOutputs
