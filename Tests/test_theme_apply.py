import sys

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.theme import get_theme_manager


def test_apply_theme_sets_stylesheet():
    app = QApplication.instance() or QApplication(sys.argv)
    tm = get_theme_manager()
    # Ensure theme contains boolean entries that used to break apply_theme
    assert isinstance(tm.theme.get("ui_font_italic"), (bool, type(None)))

    ok = tm.apply_theme(app)
    assert ok is True
    ss = app.styleSheet() or ""
    assert "QPushButton:hover" in ss

    # Clean up
    app.setStyleSheet("")
