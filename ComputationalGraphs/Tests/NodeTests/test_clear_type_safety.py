import pytest

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode


def test_setting_inputs_to_string_does_not_crash():
    g = Graph()
    x = DataStreamNode(name="x", data=[1, 2, 3])
    y = DataStreamNode(name="y", data=[10, 20, 30])
    add = AdditionNode(name="add")
    add.AddPreNode(x, y)
    g.AddNode(x, y, add)

    # Simulate accidental corruption of internal inputs attribute
    add.inputs = "corrupted"

    proc = GraphProcessor(graph=g, verbose=False)

    # Should not raise and should compute a numeric value
    proc.ComputeGraphSingleThread(iterations=1)
    assert isinstance(add.value, (int, float))


def test_buffer_reset_handles_string_buffer():
    b = BufferNode(name="buff", data=[1, 2, 3])

    # Corrupt buffer to a string
    b.buffer = "oops"

    b.ResetBuffer()

    # After reset, buffer must be a list again and value None
    assert isinstance(b.buffer, list)
    assert b.value is None
