import numpy as np

from ClassicMLP import ClassicMLP
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.SigmoidNode import SigmoidNode


def test_weight_and_bias_copy():
    rng = np.random.RandomState(1234)
    input_size = 3
    hidden_layers = [5, 2]
    output_size = 1

    weights, biases = [], []
    layer_dims = [input_size] + hidden_layers + [output_size]
    for i in range(len(layer_dims) - 1):
        w = rng.uniform(-1, 1, size=(layer_dims[i], layer_dims[i + 1]))
        b = rng.uniform(-1, 1, size=(1, layer_dims[i + 1]))
        weights.append(w)
        biases.append(b)

    classic = ClassicMLP(
        input_size=input_size,
        output_size=output_size,
        hidden_layers=hidden_layers,
        use_bias=True,
    )
    # apply
    classic.weights = [w.copy() for w in weights]
    classic.biases = [b.copy() for b in biases]

    mlp = MLPGraph(
        numInputs=input_size,
        numOutputs=output_size,
        numHiddenLayers=len(hidden_layers),
        hiddenLayerSizes=hidden_layers,
        activationFunction=SigmoidNode,
        outputLayerType=LinearNode,
        add_bias=True,
    )
    mlp.BuildMLP()

    # Assign values using same code path as experiment
    from Experiments.exp_compare_diabetes_multi_trial import apply_weights_to_graph

    apply_weights_to_graph(mlp, classic)

    # Check a few named weights and biases exist and match
    named = classic.get_named_weights()
    for wl in mlp.weightLayers:
        for row in wl:
            for node in row:
                assert node.name in named
                assert np.isclose(node.value, float(named[node.name]))

    # Bias nodes
    # Check hidden bias
    for layer_idx, brow in enumerate(mlp.biasLayers[:-1]):
        for j, bnode in enumerate(brow):
            assert np.isclose(bnode.value, float(biases[layer_idx][0, j]))

    # Output bias
    for j, bnode in enumerate(mlp.biasLayers[-1]):
        assert np.isclose(bnode.value, float(biases[-1][0, j]))
