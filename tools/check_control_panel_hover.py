"""
DEPRECATED: check_control_panel_hover.py

Manual hover-checking utility. Replaced by unit tests and removed from active use.
"""

if __name__ == "__main__":
    print("check_control_panel_hover.py is deprecated. Use unit tests instead.")


def fake_icon(name, color=None):
    called.setdefault("calls", []).append((name, color))
    # return a minimal QIcon
    from PyQt6.QtGui import QIcon

    return QIcon()


qta.icon = fake_icon
sys.modules["qtawesome"] = qta

from gui_framework.legacy import MainWindow

win = MainWindow()
play = win.play_btn
print("Play btn initial stylesheet:", repr(play.styleSheet()))
print("Play btn icon (initial empty?):", not play.icon().isNull())
from PyQt6.QtCore import QEvent

# Simulate hover enter using QApplication.sendEvent so event filters are called
from PyQt6.QtWidgets import QApplication

QApplication.sendEvent(play, QEvent(QEvent.Type.Enter))
print("After Enter stylesheet:", repr(play.styleSheet()))
print("qtawesome calls after Enter:", called)
# Simulate hover leave
QApplication.sendEvent(play, QEvent(QEvent.Type.Leave))
print("After Leave stylesheet:", repr(play.styleSheet()))
print("qtawesome calls after Leave:", called)
print("Done")
