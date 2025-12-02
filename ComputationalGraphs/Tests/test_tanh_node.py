import numpy as np

from ComputationalGraphs.Nodes.TanhDerivativeNode import TanhDerivativeNode
from ComputationalGraphs.Nodes.TanhNode import TanhNode


def test_tanh_node_operation():
    node = TanhNode(name="tanh")
    inputs = [0, 1, -1, 2, -2]
    for x in inputs:
        expected = np.tanh(x)
        out = node.Operation(x)
        assert np.isclose(
            out, expected
        ), f"TanhNode returned {out} for input {x}, expected {expected}"


def test_tanh_derivative_node_operation():
    dnode = TanhDerivativeNode(name="tanh_deriv")
    values = [
        0,
        0.5,
        -0.5,
        0.964027580075817,
        -0.964027580075817,
    ]  # tanh values for known inputs
    for val in values:
        expected = 1 - (val**2)
        out = dnode.Operation(val)
        assert np.isclose(
            out, expected
        ), f"TanhDerivativeNode returned {out} for input {val}, expected {expected}"
