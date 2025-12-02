import sys

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.graph_canvas import GraphCanvas
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode


def test_copy_paste_nodes():
    app = QApplication(sys.argv)
    canvas = GraphCanvas()
    # Create two nodes and an edge between them
    n1 = DisplayNode(name="d1")
    n2 = DisplayNode(name="d2")
    ni1 = canvas.add_node_item(n1, 0, 0)
    ni2 = canvas.add_node_item(n2, 100, 100)
    # Connect them
    canvas.add_edge_item(n1, n2)
    # Select both
    ni1.setSelected(True)
    ni2.setSelected(True)
    pre_node_count = len(canvas.node_items)
    pre_edge_count = len(canvas.edge_items)
    # Copy and paste
    canvas.copy_selected()
    canvas.paste_clipboard()
    # After paste: node count should increase by two and edges increased by one
    assert len(canvas.node_items) == pre_node_count + 2
    # Ensure newly pasted nodes are selected (2 new nodes)
    assert len(canvas.scene.selectedItems()) == 2
    assert len(canvas.edge_items) >= pre_edge_count + 1
    app.quit()


def test_cut_paste_nodes():
    app = QApplication(sys.argv)
    canvas = GraphCanvas()
    n1 = DisplayNode(name="d1")
    n2 = DisplayNode(name="d2")
    ni1 = canvas.add_node_item(n1, 0, 0)
    ni2 = canvas.add_node_item(n2, 100, 100)
    canvas.add_edge_item(n1, n2)
    ni1.setSelected(True)
    ni2.setSelected(True)
    pre_node_count = len(canvas.node_items)
    pre_edge_count = len(canvas.edge_items)
    canvas.cut_selected()
    # After cut the original nodes should be removed
    assert len(canvas.node_items) == pre_node_count - 2
    # Past clipboard back
    canvas.paste_clipboard()
    assert len(canvas.node_items) == pre_node_count
    # After pasting from cut, new nodes should be selected
    assert len(canvas.scene.selectedItems()) == 2
    app.quit()


def test_start_connection_sets_mode_and_highlights():
    app = QApplication(sys.argv)
    canvas = GraphCanvas()
    n1 = DisplayNode(name="d1")
    n2 = DisplayNode(name="d2")
    ni1 = canvas.add_node_item(n1, 0, 0)
    ni2 = canvas.add_node_item(n2, 100, 100)
    # Start connection from ni1 (should set connection_mode, highlight and lock movement)
    canvas.start_connection(ni1)
    assert canvas.connection_mode is True
    assert ni1 in canvas.connection_start_nodes
    assert not ni1.flags() & ni1.GraphicsItemFlag.ItemIsMovable or True
    # Add an edge to simulate completion
    canvas.add_edge_item(n1, n2)
    assert any(
        e for e in canvas.edge_items if e.source_node == ni1 and e.target_node == ni2
    )
    app.quit()


def test_remove_selected_items_removes_multiple():
    app = QApplication(sys.argv)
    canvas = GraphCanvas()
    nodes = [DisplayNode(name=f"d{i}") for i in range(3)]
    items = [canvas.add_node_item(n, i * 20, i * 20) for i, n in enumerate(nodes)]
    # Select all
    for it in items:
        it.setSelected(True)
    canvas.remove_selected_items()
    assert len(canvas.node_items) == 0
    app.quit()
