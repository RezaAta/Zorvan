import numpy as np

from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
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


def test_tanh_and_derivative_in_graph_manual_processing():
    from ComputationalGraphs.Core.Graph import Graph
    from ComputationalGraphs.Core.GraphProcessor import GraphProcessor

    input_values = [0, 1, -1, 2, -2]
    input_node = DataStreamNode(name="input", data=input_values)
    tanh_node = TanhNode(name="tanh")
    tanh_deriv_node = TanhDerivativeNode(name="tanh_deriv")

    g = Graph()
    g.AddNode(input_node)
    g.AddNode(tanh_node)
    g.AddNode(tanh_deriv_node)
    g.ConnectPreNode(tanh_node, input_node)
    g.ConnectPreNode(tanh_deriv_node, tanh_node)
    g.UpdateAdjacencyMatrix()

    # Run several steps and check correctness: derivative = 1 - tanh(input)^2
    # Process nodes in strict sequence directly to avoid GraphProcessor scheduling details
    for _ in range(5):
        input_node.UpdateInputs()
        input_node.ProcessBatch()
        tanh_node.UpdateInputs()
        tanh_node.ProcessBatch()
        tanh_deriv_node.UpdateInputs()
        tanh_deriv_node.ProcessBatch()
        tanh_val = tanh_node.value
        deriv_val = tanh_deriv_node.value
        assert np.isclose(
            deriv_val, 1 - tanh_val**2
        ), f"derivative {deriv_val} != 1 - tanh^2 ({1 - tanh_val ** 2})"
