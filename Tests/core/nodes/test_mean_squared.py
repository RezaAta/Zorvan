import pytest

from zorvan.Nodes.MeanSquaredNode import MeanSquaredNode


def test_mean_squared_node_computes_expected_mean_of_squares():
    node = MeanSquaredNode(name="MS", size=3, mode="continuous", allowNone=False)

    assert pytest.approx(node.Operation(1), rel=1e-9) == 1.0
    assert pytest.approx(node.Operation(2), rel=1e-9) == 2.5
    assert pytest.approx(node.Operation(3), rel=1e-9) == 14 / 3
    assert node.buffer == [1, 2, 3]
