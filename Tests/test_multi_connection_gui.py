import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QPoint

from ComputationalGraphs.GUI.graph_canvas import GraphCanvas
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode


def test_multi_connection_basic(qtbot=None):
    """Programmatic test: select multiple nodes and connect to a target node."""
    app = QApplication.instance() or QApplication(sys.argv)
    canvas = GraphCanvas()
    # Create three nodes
    n1 = DataStreamNode(name='Data1', data=[1])
    n2 = DataStreamNode(name='Data2', data=[2])
    target = DataStreamNode(name='Target', data=[0])

    ni1 = canvas.add_node_item(n1, x=0, y=0)
    ni2 = canvas.add_node_item(n2, x=100, y=0)
    nti = canvas.add_node_item(target, x=200, y=0)

    # Select both source nodes
    ni1.setSelected(True)
    ni2.setSelected(True)

    # Simulate click and drag from ni1's edge toward target
    # Start press on the edge region (near right of ni1)
    edge_point = ni1.mapToScene(ni1.output_port)
    # Map canvas coords -> viewport coords
    view_pos = canvas.mapFromScene(edge_point)

    QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, view_pos)
    # Move toward target
    target_point = nti.mapToScene(nti.input_port)
    target_view_pos = canvas.mapFromScene(target_point)
    QTest.mouseMove(canvas.viewport(), target_view_pos)
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, target_view_pos)

    # All selected source nodes should have created edges to target
    # There should be 2 edges: from n1 and n2 to target
    edges_count = len(canvas.edge_items)
    assert edges_count >= 2, f"Expected at least 2 edges, got {edges_count}"

if __name__ == '__main__':
    test_multi_connection_basic()
