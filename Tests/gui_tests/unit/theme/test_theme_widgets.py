import sys

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import get_theme_manager
from gui_framework.legacy import ThemedPushButton, ThemedScrollArea


def test_themed_push_button_updates_on_theme_change():
    app = QApplication.instance() or QApplication([])
    btn = ThemedPushButton("Test")

    tm = get_theme_manager()
    # Change a theme token and apply
    tm.set_theme({"button_bg": "#101010", "button_hover": "#202020"}, persist=False)
    tm.apply_theme()

    # The button should have a themed property so QSS will apply
    assert btn.property("themed") is True

    # If we set a direct background via theme (applied on app stylesheet),
    # the button should continue to exist and not raise applying theme
    # (no direct assertion possible for stylesheet content here in headless env)


def test_themed_scroll_area_marks_child_panel():
    app = QApplication.instance() or QApplication([])
    sa = ThemedScrollArea()

    from PyQt6.QtWidgets import QWidget

    child = QWidget()
    sa.setWidget(child)
    # Trigger apply_theme which should mark child as themed panel
    sa.apply_theme()

    assert child.property("themed_panel") == True


def test_button_hover_styles_and_cursor():
    """Ensure hover color is present in the applied stylesheet and
    themed buttons expose a pointing-hand cursor for hover affordance."""
    from PyQt6.QtCore import Qt

    app = QApplication.instance() or QApplication([])
    tm = get_theme_manager()
    tm.set_theme(
        {
            "button_bg": "#101010",
            "button_hover": "#202020",
            "button_pressed": "#303030",
        },
        persist=False,
    )
    tm.apply_theme()

    ss = app.styleSheet() or ""
    # The hover color token should be present in the resulting app stylesheet
    assert "#202020" in ss
    # The stylesheet should include hover rules for both QPushButton and themed QToolButton
    assert "QPushButton:hover" in ss
    assert 'QToolButton[themed="true"]:hover' in ss

    # Cursor should be pointing hand for themed buttons
    btn = ThemedPushButton("X")
    tbtn = ThemedToolButton()
    assert btn.cursor().shape() == Qt.CursorShape.PointingHandCursor
    assert tbtn.cursor().shape() == Qt.CursorShape.PointingHandCursor
