"""Run quick sanity checks for the icon hover filter without pytest.
"""

import sys
import types

from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QApplication, QPushButton

# Ensure QApplication exists BEFORE importing modules that create widgets
if QApplication.instance() is None:
    QApplication([])

from ComputationalGraphs.GUI.controllers.control_panel_builder import _IconHoverFilter


# Test 1: theme-derived hover color
class FakeTM:
    def __init__(self, color_hex):
        self._color = QColor(color_hex)

    def get_color(self, key, default=None):
        return self._color


fake_tm = FakeTM("#112233")

import ComputationalGraphs.GUI.theme as theme_mod

theme_mod.get_theme_manager = lambda: fake_tm

qta = types.ModuleType("qtawesome")
called = {}


def fake_icon(name, color=None):
    called["color"] = color
    return QIcon()


qta.icon = fake_icon
sys.modules["qtawesome"] = qta

btn = QPushButton()
print("Created btn for Test1")
filter_obj = _IconHoverFilter(btn, "fa-test", None, 14, "accent")
print("Instantiated filter for Test1")
try:
    filter_obj.eventFilter(btn, QEvent(QEvent.Type.Enter))
    print("EventFilter call completed for Test1")
    assert "color" in called, "qtawesome.icon was not called"
    assert (
        called["color"] == QColor("#112233").lighter(120).name()
    ), f"unexpected color {called['color']}"
    print("Test1 OK")
except Exception as e:
    import traceback

    print("Test1 Exception:")
    traceback.print_exc()
    raise


# Test 2: fallback derived from base
try:

    def raise_err():
        raise RuntimeError("no theme")

    theme_mod.get_theme_manager = raise_err
    called = {}
    qta.icon = fake_icon
    sys.modules["qtawesome"] = qta
    btn2 = QPushButton()
    filter2 = _IconHoverFilter(btn2, "fa-test", None, 14, "accent")
    filter2.eventFilter(btn2, QEvent(QEvent.Type.Enter))
    assert "color" in called, "qtawesome.icon was not called in fallback"
    assert (
        called["color"] == QColor("#4a86e8").lighter(120).name()
    ), f"unexpected fallback color {called['color']}"
    print("Test2 OK")
except Exception as e:
    print("Test2 Exception:", repr(e))
    raise
