from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel
from gui_framework.viewmodels.inspector_viewmodel import InspectorViewModel


class Node:
    def __init__(self, name, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y
        self.predecessors = []


class Graph:
    def __init__(self, nodes):
        self.nodes = nodes


def test_inspector_updates_on_selection():
    a = Node("A")
    b = Node("B")
    g = Graph([a, b])

    cvm = CanvasViewModel(g)
    cvm.initialize()

    inspector = InspectorViewModel(cvm)
    inspector.initialize()

    # Select node A
    cvm.select_node("A")
    # Trigger nodes_changed notification manually if needed
    cvm.nodes_changed += 1

    assert inspector.selected_node_id == "A"
    props = inspector.get_properties()
    assert props["name"] == "A"
    assert props["x"] == 0.0


def test_inspector_set_property_updates_canvas_and_graph():
    a = Node("A")
    a.custom = 123
    g = Graph([a])

    cvm = CanvasViewModel(g)
    cvm.initialize()

    inspector = InspectorViewModel(cvm)
    inspector.initialize()

    cvm.select_node("A")
    cvm.nodes_changed += 1

    # Set render property
    ok = inspector.set_property("color", "#FF0000")
    assert ok
    assert cvm.get_node("A").color == "#FF0000"

    # Set graph property
    ok2 = inspector.set_property("custom", 999)
    assert ok2
    assert a.custom == 999
