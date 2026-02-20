import pytest

from zorvan.Core.Graph import Graph
from zorvan.Nodes.ContainerNode import ContainerNode


def test_remove_subgraph_clears_node_subgraph_id():
    g = Graph()
    a = ContainerNode("a", value=1)
    b = ContainerNode("b", value=2)
    g.AddNode(a, b)

    sg = g.create_subgraph_from_nodes([a, b], name="S")

    # Nodes should be marked with the subgraph id
    assert getattr(a, "sub_graph_id", None) == sg.graph_id
    assert getattr(b, "sub_graph_id", None) == sg.graph_id

    # Removing the subgraph should clear node attributes and unlink
    removed = g.remove_subgraph(sg)
    assert removed is True
    assert getattr(a, "sub_graph_id", None) is None
    assert getattr(b, "sub_graph_id", None) is None


def test_restore_subgraph_from_metadata_missing_nodes_returns_none():
    g = Graph()

    # Metadata references non-existent node IDs
    meta = {
        "graph_id": "nope",
        "graph_name": "Missing",
        "graph_color": "#111111",
        "node_ids": ["not_there"],
    }

    # Empty id_map should cause restoration to fail gracefully and return None
    res = g.restore_subgraph_from_metadata(meta, id_map={})
    assert res is None
