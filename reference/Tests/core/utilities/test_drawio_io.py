import tempfile

from zorvan_reference.Core.DrawioIO import DrawioIO
from zorvan_reference.Core.Graph import Graph
from zorvan_reference.Nodes.AdditionNode import AdditionNode
from zorvan_reference.Nodes.DisplayNode import DisplayNode


def test_drawio_io_roundtrip_preserves_graph_structure(tmp_path):
    graph = Graph()
    node_a = DisplayNode("a", value=1)
    node_b = DisplayNode("b", value=2)
    node_c = AdditionNode("sum")
    node_c.AddPreNode(node_a, node_b)

    graph.AddNode(node_a, node_b, node_c)
    graph.UpdateAdjacencyMatrix()

    path = tmp_path / "roundtrip.drawio"
    DrawioIO.save(graph, str(path))
    loaded_graph = DrawioIO.load(str(path))

    assert len(loaded_graph.nodes) == 3
    assert {node.name for node in loaded_graph.nodes} == {"a", "b", "sum"}
