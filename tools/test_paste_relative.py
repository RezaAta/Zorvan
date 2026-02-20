import sys
from pathlib import Path

from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)
from zorvan.GUI.graph_canvas import GraphCanvas
from zorvan.Nodes.DisplayNode import DisplayNode

app = QApplication([])
canvas = GraphCanvas()

# Add two nodes with large positions
n1 = DisplayNode(name="A")
ni1 = canvas.add_node_item(n1, 5000, 3000)
n2 = DisplayNode(name="B")
ni2 = canvas.add_node_item(n2, 5100, 3000)

# Select them
ni1.setSelected(True)
ni2.setSelected(True)

# Copy
canvas.copy_selected()

# Place cursor at center of viewport
viewport_rect = canvas.viewport().rect()
center_local = viewport_rect.center()
global_center = canvas.mapToGlobal(center_local)
QCursor.setPos(global_center)

# Paste
canvas.paste_clipboard()

# Print new nodes positions
for node, item in canvas.node_items.items():
    print("Node:", node.name, "pos:", item.pos().x(), item.pos().y())

app.quit()
