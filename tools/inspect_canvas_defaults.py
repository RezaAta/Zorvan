import sys

sys.path.insert(
    0,
    r"c:/My Stuff/Uni & Research/Artificial Inteligence/Computational Graph/Implementations/ComputationalGraphs",
)
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.graph_canvas import GraphCanvas

app = QApplication([])
canvas = GraphCanvas()
print("grid_mode:", canvas.grid_mode)
print("grid_size:", canvas.grid_size)
print("snap_step:", canvas.snap_step)
print("snap_to_grid:", canvas.snap_to_grid)
print("show_grid:", canvas.show_grid)
app.quit()
