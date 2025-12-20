import random

import numpy as np

from ClassicMLP import ClassicMLP
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from Experiments.HybridTempPredictionComparison import copy_weights_to_classic


def test_bias_initialization_and_copy():
    """Verify biases are initialized in both models and copied identically."""
    random.seed(123)
    np.random.seed(123)

    # Build a small graph MLP and ensure biases exist and are zero-initialized
    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=1,
        hiddenLayerSizes=[3],
        add_bias=True,
    )
    mlp.BuildMLP()

    # MLPGraph biasLayers should exist and be zeros by default
    assert hasattr(mlp, "biasLayers") and len(mlp.biasLayers) == 2
    for layer in mlp.biasLayers:
        vals = np.array([b.value for b in layer])
        assert np.allclose(vals, 0.0)

    # ClassicMLP should also have zero biases when use_bias=True
    classic = ClassicMLP(input_size=2, output_size=1, hidden_layers=[3], use_bias=True)
    for b in classic.biases:
        assert b is not None
        assert np.allclose(b, 0.0)

    # Set MLPGraph biases to known non-zero values and copy into Classic
    target_hidden = np.array([0.11, -0.22, 0.33])
    for i, b in enumerate(mlp.biasLayers[0]):
        b.value = float(target_hidden[i])
    target_out = np.array([0.5])
    mlp.biasLayers[1][0].value = float(target_out[0])

    # Perform copy
    copy_weights_to_classic(mlp, classic)

    # Verify exact numeric match after copying
    assert np.allclose(classic.biases[0][0], target_hidden)
    assert np.allclose(classic.biases[1][0], target_out)
