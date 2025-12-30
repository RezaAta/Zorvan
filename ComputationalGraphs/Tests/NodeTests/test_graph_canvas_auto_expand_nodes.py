import sys

import pytest

# Skip GUI tests when PyQt6 isn't available in CI environments
pytest.importorskip("PyQt6")

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.graph_canvas import GraphCanvas
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode


def test_auto_expand_to_nodes_add_and_remove():
    created_app = False
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    canvas = GraphCanvas()
    # Default rect should match the default_scene_rect
    default_rect = canvas.default_scene_rect
    initial_scene_rect = canvas.scene.sceneRect()
    assert initial_scene_rect.width() == default_rect.width()
    assert initial_scene_rect.height() == default_rect.height()

    # Record center before adding nodes
    canvas.resize(800, 600)
    canvas.show()
    app.processEvents()
    center_before = canvas.scene.sceneRect().center()

    # Add a node far from origin
    node = DisplayNode(name="d")
    ni = canvas.add_node_item(node, x=5000, y=3000)

    # After adding, the scene rect must include the new node (with padding)
    rect = canvas.scene.sceneRect()
    assert rect.contains(QPointF(5000, 3000))
    # Check that right edge is at least node x + radius + padding
    assert rect.right() >= 5000 + ni.radius + canvas.canvas_padding

    # Now remove the node and ensure scene rect shrinks but is not smaller than default
    ni.setSelected(True)
    canvas.remove_selected_items()
    app.processEvents()
    rect2 = canvas.scene.sceneRect()
    assert rect2.width() >= default_rect.width()
    assert rect2.height() >= default_rect.height()

    # Ensure center preserved after updates
    center_after = canvas.scene.sceneRect().center()
    assert abs(center_before.x() - center_after.x()) < 0.01
    assert abs(center_before.y() - center_after.y()) < 0.01

    try:
        canvas.close()
    except Exception:
        pass
    if created_app:
        app.quit()


def test_click_does_not_recenter():
    created_app = False
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    canvas = GraphCanvas()
    canvas.resize(800, 600)
    canvas.show()
    app.processEvents()
    # Add a node and set a center away from origin
    node = DisplayNode(name="d")
    ni = canvas.add_node_item(node, x=0, y=0)
    canvas.centerOn(1000, 1000)
    app.processEvents()
    center_before = canvas.mapToScene(canvas.viewport().rect().center())

    # Simulate left click on node
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    pos = canvas.mapFromScene(ni.scenePos())
    QTest.mouseClick(
        canvas.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pos,
    )
    app.processEvents()
    center_after = canvas.mapToScene(canvas.viewport().rect().center())
    assert abs(center_before.x() - center_after.x()) < 1e-3
    assert abs(center_before.y() - center_after.y()) < 1e-3

    # Simulate right click on node
    QTest.mouseClick(
        canvas.viewport(),
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        pos,
    )
    app.processEvents()
    center_after2 = canvas.mapToScene(canvas.viewport().rect().center())
    assert abs(center_before.x() - center_after2.x()) < 1e-3
    assert abs(center_before.y() - center_after2.y()) < 1e-3

    try:
        canvas.close()
    except Exception:
        pass
    if created_app:
        app.quit()
