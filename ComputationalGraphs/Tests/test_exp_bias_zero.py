import numpy as np

import Experiments.exp_compare_diabetes_multi_trial as exp
from ClassicMLP import ClassicMLP
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode


def test_generate_initial_biases_are_zero():
    rng = np.random.RandomState(42)
    weights, biases = exp.generate_initial_weights_and_biases(
        rng, input_size=5, hidden_layers=[3], output_size=1, use_bias=True
    )
    # biases is a list of arrays (1 x n_out) for each layer; check all are zeros
    for b in biases:
        assert b is not None
        assert np.allclose(b, 0.0)


def test_apply_weights_zero_biases_propagated():
    rng = np.random.RandomState(42)
    weights, biases = exp.generate_initial_weights_and_biases(
        rng, input_size=4, hidden_layers=[2], output_size=1, use_bias=True
    )

    classic = ClassicMLP(
        input_size=4,
        output_size=1,
        hidden_layers=[2],
        learning_rate=0.01,
        use_bias=True,
    )
    exp.apply_weights_to_classic(classic, weights, biases)

    # classic.biases should be zeros
    for b in classic.biases:
        assert b is not None
        assert np.allclose(b, 0.0)

    mlp_graph = MLPGraph(
        numInputs=4,
        numOutputs=1,
        numHiddenLayers=1,
        hiddenLayerSizes=[2],
        activationFunction=SigmoidNode,
        outputLayerType=LinearNode,
        add_bias=True,
        use_bias=True,
    )
    mlp_graph.BuildMLP()
    exp.apply_weights_to_graph(mlp_graph, classic)

    # Check bias ContainerNodes in mlp_graph are zero
    for bl in mlp_graph.biasLayers:
        for bnode in bl:
            assert float(bnode.value) == 0.0
