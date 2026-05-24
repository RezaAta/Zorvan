import sys
import types

from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QApplication, QPushButton

if QApplication.instance() is None:
    app = QApplication([])

from gui_framework.legacy import _IconHoverFilter


# Fake TM
class FakeTM:
    def __init__(self, c):
        self._c = QColor(c)

    def get_color(self, key, default=None):
        return self._c


fake_tm = FakeTM("#112233")
import gui_framework.legacy as theme_mod

theme_mod.get_theme_manager = lambda: fake_tm

qta = types.ModuleType("qtawesome")
called = {}


def fake_icon(name, color=None):
    called["color"] = color
    return QIcon()


qta.icon = fake_icon
sys.modules["qtawesome"] = qta

btn = QPushButton("test")
filter_obj = _IconHoverFilter(btn, "fa-test", None, 14, "accent")
print("Before Enter called:", called)
filter_obj.eventFilter(btn, QEvent(QEvent.Type.Enter))
print("After Enter called:", called)
filter_obj.eventFilter(btn, QEvent(QEvent.Type.Leave))
print("After Leave called:", called)
print("Expected base color:", QColor("#112233").name())
