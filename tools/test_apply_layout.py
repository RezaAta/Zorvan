import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)
from zorvan.GUI.examples_loader import ExamplesLoader
from zorvan.GUI.graph_canvas import GraphCanvas

app = QApplication([])
loader = ExamplesLoader()
g = loader._build_piecewise_mlp2_concurrent()
canvas = GraphCanvas(None)
canvas.graph = g
for idx, n in enumerate(g.nodes):
    canvas.add_node_item(n, idx * 10, idx * 15)
pos = canvas.apply_layout("ann")
print("apply_layout returned type:", type(pos), "len:", len(pos))
count = 0
for n, p in list(pos.items())[:10]:
    print(getattr(n, "name", str(n)), p)
app.quit()
