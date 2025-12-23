from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode


def test_set_subgraph_color_by_object_and_id():
    g = Graph()
    a = ContainerNode("a", value=1)
    b = ContainerNode("b", value=2)
    g.AddNode(a, b)

    sub = g.create_subgraph_from_nodes([a, b], name="S")
    assert sub in g.sub_graphs

    # Set by object
    res = g.set_subgraph_color(sub, "#112233")
    assert res is True
    assert sub.graph_color == "#112233"

    # Set by id
    res2 = g.set_subgraph_color(sub.graph_id, "#abcdef")
    assert res2 is True
    assert sub.graph_color == "#abcdef"


def test_set_subgraph_color_invalid_returns_false():
    g = Graph()
    res = g.set_subgraph_color("nonexistent", "#000000")
    assert res is False
