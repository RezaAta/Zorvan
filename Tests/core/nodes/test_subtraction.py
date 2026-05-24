from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.ContainerNode import ContainerNode
from zorvan.Nodes.SubtractionNode import SubtractionNode


def test_subtraction_node_computes_first_input_minus_second_input():
    sub_node = SubtractionNode(name="result")

    assert sub_node.Operation(10.0, 3.0) == 7.0
