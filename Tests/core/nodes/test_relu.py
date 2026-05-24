from zorvan.Nodes.ReLUDerivativeNode import ReLUDerivativeNode
from zorvan.Nodes.ReLUNode import ReLUNode


def test_relu_node_clamps_negative_values_to_zero():
    relu = ReLUNode("ReLU")

    assert relu.Operation(-0.28) == 0
    assert relu.Operation(1.5) == 1.5


def test_relu_derivative_node_computes_expected_gradient():
    derivative = ReLUDerivativeNode("Derivative")

    assert derivative.Operation(0.0) == 0.0
    assert derivative.Operation(0.5) == 1
