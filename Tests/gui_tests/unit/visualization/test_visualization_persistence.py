import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow
from gui_framework.legacy import get_theme_manager


def test_visualization_colors_persist_across_restarts(tmp_path):
    app = QApplication.instance() or QApplication([])
    # Create a window and set custom colors via controller
    mw = MainWindow()
    vc = mw.visualization_controller

    # Pick unusual colors
    mw.min_gradient_color = QColor(1, 2, 3)
    mw.max_gradient_color = QColor(4, 5, 6)
    mw.default_node_color = QColor(7, 8, 9)
    mw.default_text_color = QColor(10, 11, 12)

    # Apply to persist
    vc.apply_node_colors()

    # Direct check that QSettings contain persisted values
    from gui_framework.legacy import get_theme_manager

    tm = get_theme_manager()
    assert (
        tm.settings.value("visualization/min_gradient_color")
        == mw.min_gradient_color.name()
    )
    assert (
        tm.settings.value("visualization/max_gradient_color")
        == mw.max_gradient_color.name()
    )
    assert (
        tm.settings.value("visualization/default_node_color")
        == mw.default_node_color.name()
    )
    assert (
        tm.settings.value("visualization/default_text_color")
        == mw.default_text_color.name()
    )

    # Create a fresh MainWindow which should load persisted colors
    mw2 = MainWindow()
    assert mw2.min_gradient_color.name() == mw.min_gradient_color.name()
    assert mw2.max_gradient_color.name() == mw.max_gradient_color.name()
    assert mw2.default_node_color.name() == mw.default_node_color.name()
    assert mw2.default_text_color.name() == mw.default_text_color.name()
