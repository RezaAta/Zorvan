"""
Tests for Graph subgraph support and color operations.
"""

from zorvan.Core.Graph import Graph
from zorvan.Nodes.ContainerNode import ContainerNode


def test_remove_subgraph_clears_node_subgraph_id():
    g = Graph()
    a = ContainerNode("a", value=1)
    b = ContainerNode("b", value=2)
    g.AddNode(a, b)

    sg = g.create_subgraph_from_nodes([a, b], name="S")

    assert getattr(a, "sub_graph_id", None) == sg.graph_id
    assert getattr(b, "sub_graph_id", None) == sg.graph_id

    removed = g.remove_subgraph(sg)

    assert removed is True
    assert getattr(a, "sub_graph_id", None) is None
    assert getattr(b, "sub_graph_id", None) is None


def test_restore_subgraph_from_metadata_missing_nodes_returns_none():
    g = Graph()

    meta = {
        "graph_id": "nope",
        "graph_name": "Missing",
        "graph_color": "#111111",
        "node_ids": ["not_there"],
    }

    res = g.restore_subgraph_from_metadata(meta, id_map={})
    assert res is None


def test_set_subgraph_color_by_object_and_id():
    g = Graph()
    a = ContainerNode("a", value=1)
    b = ContainerNode("b", value=2)
    g.AddNode(a, b)

    sub = g.create_subgraph_from_nodes([a, b], name="S")
    assert sub in g.sub_graphs

    res = g.set_subgraph_color(sub, "#112233")
    assert res is True
    assert sub.graph_color == "#112233"

    res2 = g.set_subgraph_color(sub.graph_id, "#abcdef")
    assert res2 is True
    assert sub.graph_color == "#abcdef"


def test_set_subgraph_color_invalid_returns_false():
    g = Graph()
    res = g.set_subgraph_color("nonexistent", "#000000")
    assert res is False
