import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[3]),
)
from PyQt6.QtWidgets import QApplication

from zorvan.GUI.graph_canvas import GraphCanvas


def test_default_grid_and_snap():
    app = QApplication([])
    canvas = GraphCanvas(None)
    assert canvas.grid_mode == "4x4"
    assert canvas.grid_size == max(1, int(canvas.node_diameter / 4))
    assert canvas.snap_step == 1
    app.quit()
