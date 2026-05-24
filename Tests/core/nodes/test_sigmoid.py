import math

import pytest

from zorvan.Nodes.SigmoidNode import SigmoidNode


def test_sigmoid_node_outputs_values_between_zero_and_one():
    node = SigmoidNode(name="Sigmoid")

    assert pytest.approx(node.Operation(0.0), rel=1e-9) == 0.5
    assert pytest.approx(node.Operation(2.0), rel=1e-9) == 1 / (1 + math.exp(-2.0))
