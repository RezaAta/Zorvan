import sys

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from zorvan.GUI.main_window import MainWindow
from zorvan.GUI.theme_widgets import ThemedPushButton, ThemedScrollArea


def test_control_panel_uses_themed_scroll_and_buttons():
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()

    # control_dock widget contains a scroll area created by ControlPanelBuilder
    scroll = mw.control_dock.widget()
    # The top-level returned widget should be a scroll area; check for themed property
    assert isinstance(scroll, ThemedScrollArea) or scroll.property("themed") is True

    # Some controls should be ThemedPushButton instances via the _create_standard_button helper
    assert hasattr(mw, "min_color_btn")
    assert hasattr(mw, "max_color_btn")
    assert hasattr(mw, "node_color_btn")
    assert isinstance(mw.min_color_btn, ThemedPushButton)
    assert isinstance(mw.max_color_btn, ThemedPushButton)
    assert isinstance(mw.node_color_btn, ThemedPushButton)

    # Also the Clear ANN button
    assert isinstance(mw.clear_ann_colors_btn, ThemedPushButton)

    # Speed slider should be a themed slider when available
    from zorvan.GUI.theme_widgets import (
        ThemedCheckBox,
        ThemedComboBox,
        ThemedSlider,
        ThemedSpinBox,
    )

    assert (
        isinstance(mw.speed_slider, ThemedSlider)
        or mw.speed_slider.property("themed") is True
    )

    # Checkboxes and combos should be themed
    assert (
        isinstance(mw.colorize_check, ThemedCheckBox)
        or mw.colorize_check.property("themed") is True
    )
    assert (
        isinstance(mw.ann_colors_check, ThemedCheckBox)
        or mw.ann_colors_check.property("themed") is True
    )
    assert (
        isinstance(mw.processor_combo, ThemedComboBox)
        or mw.processor_combo.property("themed") is True
    )
    assert (
        isinstance(mw.speed_spin, ThemedSpinBox)
        or mw.speed_spin.property("themed") is True
    )


def test_play_button_is_themed_and_hover_applies():
    app = QApplication.instance() or QApplication([])
    from zorvan.GUI.theme import get_theme_manager

    tm = get_theme_manager()
    # Ensure theme is applied so QSS contains hover rules
    tm.set_theme(
        {
            "button_bg": "#101010",
            "button_hover": "#202020",
            "button_pressed": "#303030",
        },
        persist=False,
    )
    tm.apply_theme()

    mw = MainWindow()
    assert hasattr(mw, "play_btn")
    btn = mw.play_btn
    assert btn.property("themed") is True

    ss = app.styleSheet() or ""
    assert 'QPushButton[themed="true"]:hover' in ss
    assert tm.get_color("button_hover").name() in ss
