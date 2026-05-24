import sys

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow
from gui_framework.legacy import ThemedLabel, ThemedPushButton


def test_toolbar_widgets_are_themed_when_available():
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()

    # Search label should be a ThemedLabel or have themed property
    toolbar_widgets = [
        w for w in mw.findChildren(ThemedLabel) if isinstance(w, ThemedLabel)
    ]
    # If no ThemedLabel found, check the search_box themed property
    has_themed_label = bool(toolbar_widgets)
    assert has_themed_label or mw.search_box.property("themed") is True

    # Next button and add-to-plot should be themed (either ThemedPushButton or ThemedToolButton or have themed property)
    is_push = isinstance(mw.toolbar_add_to_plot_btn, ThemedPushButton)
    is_themed_prop = bool(mw.toolbar_add_to_plot_btn.property("themed"))
    assert is_push or is_themed_prop
