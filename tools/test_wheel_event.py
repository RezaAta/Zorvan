import sys
from pathlib import Path

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QApplication

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)
from zorvan.GUI.graph_canvas import GraphCanvas

app = QApplication([])
canvas = GraphCanvas()
print("Current scale m11 before:", canvas.transform().m11())
try:
    # pos QPointF, globalPos QPointF, pixelDelta QPoint, angleDelta QPoint, buttons, modifiers, phase, inverted
    ev = QWheelEvent(
        QPointF(0, 0),
        QPointF(0, 0),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )
    canvas.wheelEvent(ev)
    print("After wheelEvent m11:", canvas.transform().m11())
except Exception as e:
    print("Wheel event creation/call failed:", e)

print("Done")
