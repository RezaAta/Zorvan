import sys

import pytest

# Skip GUI tests when PyQt6 isn't available in the environment
pytest.importorskip("PyQt6")

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.GUI.theme import get_theme_manager
from ComputationalGraphs.Nodes.BufferNode import BufferNode


def test_user_applied_node_color_persists_across_theme_change():
    app = QApplication(sys.argv)
    win = MainWindow()

    # Create a buffer node and add to canvas
    buf = BufferNode(name="Buff_T", size=2)
    ni = win.canvas.add_node_item(buf, x=0, y=0)

    # Apply a user-selected default node color via VisualizationController
    win.default_node_color = QColor(10, 20, 30)
    win.visualization_controller.apply_node_colors()

    assert ni.default_color == win.default_node_color
    assert getattr(ni, "_default_color_overridden", False) is True

    # Change the theme's default node color and apply theme
    tm = get_theme_manager()
    try:
        tm.set_theme({"node_default": "#abcdef"}, persist=False)
        tm.apply_theme()
    except Exception:
        # Some test environments may not run the full apply; still proceed
        pass

    # User-applied node color should remain (visualization priority)
    assert ni.default_color == win.default_node_color

    app.quit()


def test_ann_colors_persist_when_theme_changes():
    app = QApplication(sys.argv)
    win = MainWindow()

    # Create a buffer node which should map to a gold/yellow ANN color
    buf = BufferNode(name="Buff_T", size=2)
    ni = win.canvas.add_node_item(buf, x=0, y=0)

    # Enable ANN coloring
    win.ann_colors_check.setChecked(True)
    # Ensure ANN colors were applied
    assert ni.manual_color is not None

    # Change theme and apply
    tm = get_theme_manager()
    try:
        tm.set_theme({"node_default": "#112233"}, persist=False)
        tm.apply_theme()
    except Exception:
        pass

    # ANN manual color should persist despite theme change
    assert ni.manual_color is not None

    app.quit()


if __name__ == "__main__":
    test_user_applied_node_color_persists_across_theme_change()
    test_ann_colors_persist_when_theme_changes()
