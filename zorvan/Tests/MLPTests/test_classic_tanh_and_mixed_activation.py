import numpy as np

from ClassicMLP import ClassicMLP


def test_classic_mlp_tanh_support():
    mlp = ClassicMLP(
        input_size=1,
        output_size=1,
        hidden_layers=[1],
        hidden_activation="tanh",
        output_activation="linear",
    )

    # simple forward test
    x = np.array([[0.0]])
    out = mlp.predict(x)
    assert out.shape == (1, 1)

    # check tanh activation derivative via internal method (uses activation output)
    a = np.array([[0.0]])
    deriv = mlp._activation_derivative(np.tanh(a), "tanh")
    assert np.allclose(deriv, 1 - np.tanh(a) ** 2)


def test_classic_mlp_mixed_hidden_activations():
    # Two hidden layers with different activations
    mlp = ClassicMLP(
        input_size=2,
        output_size=1,
        hidden_layers=[2, 2],
        hidden_activation=["tanh", "sigmoid"],
    )

    # forward pass should accept a list of activations
    X = np.array([[0.1, -0.2]])
    activations = mlp.forward_pass(X)
    assert len(activations) == 1 + len(mlp.hidden_layers) + 1

    # ensure no exception on backward pass with these activations
    y = np.array([[0.3]])
    mlp.backward_pass(X, y, activations)
