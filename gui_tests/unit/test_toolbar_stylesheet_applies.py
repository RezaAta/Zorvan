from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.theme import get_theme_manager


def test_toolbar_text_color_in_stylesheet():
    app = QApplication.instance() or QApplication([])
    tm = get_theme_manager()
    # Use a distinct text color to detect in stylesheet
    tm.set_theme({"text": "#123456", "header_bg": "#abcdef"}, persist=False)
    # Apply theme (in test mode apply_theme sets stylesheet and emits theme_changed)
    tm.apply_theme()
    ss = app.styleSheet()
    assert "QToolBar" in ss
    # Ensure toolbar action selectors explicitly reference the text color
    assert "QToolBar QToolButton" in ss or "QToolBar QPushButton" in ss
    assert "#123456" in ss
