import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)
from gui_framework.legacy import ExamplesLoader, MainWindow

app = QApplication(sys.argv)
loader = ExamplesLoader()
# Large example builder
try:
    g = loader._build_piecewise_mlp2_concurrent()
except Exception:
    g = loader.categories["basic"].examples[0][2]()

mw = MainWindow()

# set graph and visualize
mw.set_graph(g)
mw._visualize_graph_on_canvas(g)

# Print scene rect and center
rect = mw.canvas.scene.sceneRect()
print("Scene rect:", rect.left(), rect.right(), rect.top(), rect.bottom())
print(
    "View center scene coords:",
    mw.canvas.mapToScene(mw.canvas.viewport().rect().center()),
)
print("Scene center", rect.center())

app.quit()
