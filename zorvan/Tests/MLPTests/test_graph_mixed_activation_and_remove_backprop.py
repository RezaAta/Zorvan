from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.SigmoidNode import SigmoidNode
from zorvan.Nodes.TanhNode import TanhNode


def test_mlp_mixed_layer_activations():
    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=2,
        hiddenLayerSizes=[2, 2],
        hiddenActivationFunctions=[TanhNode, SigmoidNode],
    )
    mlp.BuildMLP()

    # Check that first hidden layer activations are TanhNode and second are SigmoidNode
    first_layer_acts = [n[1].__class__.__name__ for n in mlp.hiddenLayers[0]]
    assert all(name == "TanhNode" for name in first_layer_acts)

    second_layer_acts = [n[1].__class__.__name__ for n in mlp.hiddenLayers[1]]
    assert all(name == "SigmoidNode" for name in second_layer_acts)


def test_remove_backprop_from_graph():
    mlp = MLPGraph(numInputs=2, numOutputs=1, numHiddenLayers=1, hiddenLayerSizes=[2])
    mlp.BuildMLP()
    backprop = BackpropGraph(mlp, learningRate=0.01)
    backprop.BuildBackprop()

    full_graph = Graph()
    for n in mlp.nodes:
        full_graph.AddNode(n)
    for n in backprop.nodes:
        full_graph.AddNode(n)

    # Ensure some typical backprop nodes exist
    names = [getattr(n, "name", "") for n in full_graph.nodes]
    assert any(
        n.startswith("EG_") or n.startswith("LRMult_") or n.startswith("D_y")
        for n in names
    )

    # Remove backprop
    BackpropGraph.RemoveBackpropFromGraph(full_graph)

    # Now ensure none of these patterns remain
    names_after = [getattr(n, "name", "") for n in full_graph.nodes]
    assert not any(
        n.startswith("EG_") or n.startswith("LRMult_") or n.startswith("D_y")
        for n in names_after
    )


def test_backprop_adds_bias_recalcs():
    # Build MLP with biases enabled
    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=1,
        hiddenLayerSizes=[2],
        add_bias=True,
    )
    mlp.BuildMLP()
    # sanity: biases created
    bias_names = [n.name for n in mlp.nodes if getattr(n, "name", "").startswith("B_")]
    assert any(n.startswith("B_H") for n in bias_names) or any(
        n.startswith("B_y") for n in bias_names
    )

    backprop = BackpropGraph(mlp, learningRate=0.01)
    backprop.BuildBackprop()

    # In backprop graph, bias nodes should have dB predecessors
    # Combine into full graph
    full_graph = Graph()
    for n in mlp.nodes:
        full_graph.AddNode(n)
    for n in backprop.nodes:
        full_graph.AddNode(n)

    # Find bias nodes and check they have predecessors added (dB_ nodes)
    bias_nodes = [
        n for n in full_graph.nodes if getattr(n, "name", "").startswith("B_")
    ]
    assert bias_nodes, "No bias nodes found in combined graph"
    found_dB = False
    for b in bias_nodes:
        if any(
            getattr(pre, "name", "").startswith("dB_")
            for pre in getattr(b, "predecessors", [])
        ):
            found_dB = True
            break
    assert found_dB, "Bias nodes do not have dB predecessors after adding backprop"
