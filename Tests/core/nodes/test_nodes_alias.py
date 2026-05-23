import os

import pytest

from zorvan.Core.CGJsonIO import load, save
from zorvan.Core.Graph import Graph
from zorvan.Nodes.AbstractNode import AbstractNode
from zorvan.Nodes.AdditionNode import AdditionNode
from zorvan.Nodes.CompressedNode import CompressedNode


def test_abstractnode_nodes_property():
    a1 = AdditionNode("a1")
    a2 = AdditionNode("a2")
    abstract = AbstractNode("A", nodes=[a1, a2])

    # nodes should be a list with the supplied internal nodes
    assert isinstance(abstract.nodes, list)
    assert abstract.nodes == [a1, a2]

    # assignment via nodes should update the internal list
    abstract.nodes = [a2]
    assert abstract.nodes == [a2]


def test_compressednode_nodes_property():
    a1 = AdditionNode("a1")
    a2 = AdditionNode("a2")
    compressed = CompressedNode("C", [a1, a2])

    assert isinstance(compressed.nodes, list)
    assert compressed.nodes == [a1, a2]

    compressed.nodes = [a2]
    assert compressed.nodes == [a2]
    assert compressed.value == a2.value


def test_cgjsonio_nodes_on_load(tmp_path):
    # Create a small graph with a compressed node, save and reload it
    g = Graph()
    a = AdditionNode("a")
    b = AdditionNode("b")
    g.AddNode(a, b)
    g.ConnectPreNode(b, a)
    g.analyze_topology()

    compressed = g.CompressNodes([a, b])

    file_path = tmp_path / "temp.cgjson"
    save(g, str(file_path))

    loaded = load(str(file_path))
    loaded_compressed = next(
        (n for n in loaded.nodes if type(n).__name__ == "CompressedNode"), None
    )
    assert loaded_compressed is not None

    # Internal nodes should be accessible via .nodes
    assert hasattr(loaded_compressed, "nodes")
    assert len(loaded_compressed.nodes) >= 1
