import sys

import pytest

# Skip GUI tests when PyQt6 isn't available in the environment
pytest.importorskip("PyQt6")

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.Nodes.BufferNode import BufferNode


def test_apply_node_colors_clears_ann_override():
    created_app = False
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    win = MainWindow()

    # Create a buffer node and add to canvas
    buf = BufferNode(name="Buff_T", size=2)
    ni = win.canvas.add_node_item(buf, x=0, y=0)

    # Apply ANN colors to ensure it sets manual_color
    win.ann_colors_check.setChecked(True)
    assert ni.manual_color is not None

    # Change default node color and apply to all nodes
    win.default_node_color = QColor(10, 20, 30)
    win.visualization_controller.apply_node_colors()

    # After applying base colors, manual_color should be cleared and default_color applied
    assert ni.manual_color is None
    assert ni.default_color == win.default_node_color

    # Close window and quit app only if this test created it
    try:
        win.close()
    except Exception:
        pass
    if created_app:
        app.quit()


if __name__ == "__main__":
    test_apply_node_colors_clears_ann_override()
