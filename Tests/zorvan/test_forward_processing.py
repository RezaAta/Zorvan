from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.AdditionNode import AdditionNode
from zorvan.Nodes.ContainerNode import ContainerNode
from zorvan.Nodes.MultiplicationNode import MultiplicationNode


def node_names(sequence):
    return [[node.name for node in step] for step in sequence]


def test_forward_processing_sequence_linear_chain():
    a = ContainerNode("a", value=1.0)
    b = AdditionNode("b")
    c = MultiplicationNode("c")
    d = AdditionNode("d")

    b.AddPreNode(a)
    c.AddPreNode(b)
    d.AddPreNode(c)

    graph = Graph()
    graph.AddNode(a, b, c, d)
    graph.UpdateAdjacencyMatrix()

    processor = GraphProcessor(graph)
    sequence = processor.find_execution_sequence(starting_nodes=[a])["sequence"]

    assert node_names(sequence) == [["a"], ["b"], ["c"], ["d"]]


def test_forward_processing_sequence_diamond_graph():
    a = ContainerNode("a", value=2.0)
    b = AdditionNode("b")
    c = MultiplicationNode("c")
    d = AdditionNode("d")

    b.AddPreNode(a)
    c.AddPreNode(a)
    d.AddPreNode(b, c)

    graph = Graph()
    graph.AddNode(a, b, c, d)
    graph.UpdateAdjacencyMatrix()

    processor = GraphProcessor(graph)
    sequence = processor.find_execution_sequence(starting_nodes=[a])["sequence"]

    assert len(sequence) == 3
    assert node_names(sequence)[0] == ["a"]
    assert set(node_names(sequence)[1]) == {"b", "c"}
    assert node_names(sequence)[2] == ["d"]
