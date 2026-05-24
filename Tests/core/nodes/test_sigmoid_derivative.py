import pytest

from zorvan.Nodes.SigmoidDerivativeNode import SigmoidDerivativeNode


def test_sigmoid_derivative_node_computes_derivative_of_sigmoid_output():
    node = SigmoidDerivativeNode("sigmoid derivative")

    assert pytest.approx(node.Operation(0.5), rel=1e-9) == 0.25
    assert pytest.approx(node.Operation(0.7310585786300049), rel=1e-9) == 0.19661193324148185
