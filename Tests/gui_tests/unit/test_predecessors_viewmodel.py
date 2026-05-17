"""Unit tests for PredecessorsViewModel."""

from gui_framework.viewmodels.dialogs.predecessors_viewmodel import (
    PredecessorsViewModel,
)


class DummyEdge:
    def __init__(
        self, src=None, tgt=None, source_node_item=None, target_node_item=None
    ):
        self.src = src
        self.tgt = tgt
        self.source_node = source_node_item
        self.target_node = target_node_item
        self._removed = False

    def remove(self):
        self._removed = True


class DummyNode:
    def __init__(self, name):
        self.name = name
        self.predecessors = []


class DummyCanvas:
    def __init__(self):
        self.edge_items = []
        self.graph = None


class DummyGraph:
    def __init__(self, nodes):
        self.nodes = nodes
        self.idToNodeDictionary = {
            getattr(n, "id", None): n
            for n in nodes
            if getattr(n, "id", None) is not None
        }

    def DisconnectPreNode(self, node, pred):
        node.predecessors = [
            p
            for p in node.predecessors
            if p is not pred and getattr(p, "name", None) != getattr(pred, "name", None)
        ]


def test_refresh_collects_predecessors_from_graph_and_canvas():
    a = DummyNode("A")
    b = DummyNode("B")
    c = DummyNode("C")
    # b is predecessor of a in graph
    a.predecessors = [b]

    graph = DummyGraph([a, b, c])
    canvas = DummyCanvas()
    canvas.graph = graph

    class NodeItem:
        def __init__(self, node):
            self.node = node

    node_item = NodeItem(a)

    # Add a canvas-only edge from c->a (use same NodeItem instance for target)
    edge = DummyEdge(
        source_node_item=type("SN", (), {"node": c})(), target_node_item=node_item
    )
    canvas.edge_items.append(edge)

    vm = PredecessorsViewModel()
    vm.load(node_item, canvas)

    preds = vm.get_predecessors()
    names = sorted([p.name for p in preds])
    assert names == ["B", "C"]


def test_disconnect_removes_graph_and_canvas_edges():
    a = DummyNode("A")
    b = DummyNode("B")
    a.predecessors = [b]
    graph = DummyGraph([a, b])
    canvas = DummyCanvas()
    canvas.graph = graph

    class NodeItem:
        def __init__(self, node):
            self.node = node

    node_item = NodeItem(a)

    # canvas edge
    edge = DummyEdge(
        src=b,
        tgt=a,
        source_node_item=type("SN", (), {"node": b})(),
        target_node_item=type("TN", (), {"node": a})(),
    )
    canvas.edge_items.append(edge)

    vm = PredecessorsViewModel()
    vm.load(node_item, canvas)

    assert any(p.name == "B" for p in vm.get_predecessors())

    ok = vm.disconnect(b)
    assert ok
    assert all(p.name != "B" for p in vm.get_predecessors())
    # canvas edge removed flag
    assert edge._removed or all(e is not edge for e in canvas.edge_items)
