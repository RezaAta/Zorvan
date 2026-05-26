import sys

import pytest

# Skip GUI tests when PyQt6 isn't available in the environment
pytest.importorskip("PyQt6")

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import GraphCanvas, NodeItem
from zorvan.Nodes.BufferNode import BufferNode


def test_manual_color_init_and_ann_apply():
    created_app = False
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    canvas = GraphCanvas()

    # Create a BufferNode and a NodeItem
    buf = BufferNode(name="Buff_T", size=3)
    buf.value = 0.5
    ni = canvas.add_node_item(buf, x=10, y=10)

    # The NodeItem should have a manual_color attribute initialized
    assert hasattr(ni, "manual_color"), "manual_color not present on NodeItem"
    assert ni.manual_color is None

    # Apply ANN colors on canvas via the visualization controller
    mw = None
    try:
        # Create a MainWindow to access visualization controller for clear testing
        from gui_framework.legacy import MainWindow

        mw = MainWindow()
        # Transfer node item to the main window canvas for full UI integration
        mw.canvas = canvas
    except Exception:
        pass

    # Apply ANN colors on canvas and ensure this node receives manual color
    canvas.apply_ann_colors()
    assert (
        ni.manual_color is not None
    ), "ANN color not applied to node in apply_ann_colors"

    # Add a new node while ANN colors are active; it should receive an ANN color immediately
    buf2 = BufferNode(name="Buff_G", size=2)
    ni2 = canvas.add_node_item(buf2, x=100, y=150)
    assert hasattr(ni2, "manual_color")
    assert (
        ni2.manual_color is not None
    ), "New node did not get ANN color when canvas had ANN color mode active"

    # Clear ANN colors and verify they are cleared
    # Use UI clear handler to clear both ANN and value-based colors if available
    if mw is not None:
        mw.visualization_controller.clear_colors()
    else:
        # Fallback to direct canvas API
        canvas.clear_ann_colors()
    assert ni.manual_color is None
    assert ni2.manual_color is None

    # Quit application if this test created it
    if created_app:
        app.quit()
