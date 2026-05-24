import sys
from pathlib import Path

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)
from gui_framework.legacy import GraphCanvas
from zorvan.Nodes.DisplayNode import DisplayNode

app = QApplication([])
canvas = GraphCanvas()

# Add an initial node at origin
n = DisplayNode(name="test")
ni = canvas.add_node_item(n, 0, 0)
ni.setSelected(True)

# Copy selected
canvas.copy_selected()

# Place the cursor at some spot within the viewport by mapping a known center
# We will simulate cursor position by mapping canvas viewport center into global coords
viewport_rect = canvas.viewport().rect()
center_local = viewport_rect.center()
global_center = canvas.mapToGlobal(center_local)
QCursor.setPos(global_center)

# Paste
canvas.paste_clipboard()

# Inspect pasted nodes (should be one copy)
pasted_nodes = [
    n
    for n in canvas.node_items.keys()
    if n.name and n.name.startswith("Copy_") or n.name == "test"
]
print("Number of nodes in canvas:", len(canvas.node_items))
# Print positions to help validate
for node, item in canvas.node_items.items():
    print(
        "Node:",
        getattr(node, "name", "unknown"),
        "pos:",
        float(item.pos().x()),
        float(item.pos().y()),
    )

print("Done")
