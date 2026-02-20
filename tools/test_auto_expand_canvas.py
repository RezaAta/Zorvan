import sys

from PyQt6.QtWidgets import QApplication

from zorvan.GUI.graph_canvas import GraphCanvas
from zorvan.Nodes.DisplayNode import DisplayNode

app = QApplication([])
canvas = GraphCanvas()

n = DisplayNode(name="d")
ni = canvas.add_node_item(n, x=5000, y=3000)

rect = canvas.scene.sceneRect()
print(
    "Scene rect left,right,top,bottom:",
    rect.left(),
    rect.right(),
    rect.top(),
    rect.bottom(),
)
print("Node pos", ni.pos().x(), ni.pos().y())
print("Contains node? ", rect.contains(ni.pos()))

# Now clear and add node via manual visualization (simulate large graph) - create node by direct add
canvas2 = GraphCanvas()
ni2 = canvas2.node_items
# simulate direct add
node = DisplayNode(name="big")
ni_item = None
from zorvan.GUI.node_item import NodeItem

ni_item = NodeItem(node, 5000, 3000)
canvas2.scene.addItem(ni_item)
canvas2.node_items[node] = ni_item
# simulate finalize visual (call update_scene_rect normally called by main_window)
canvas2._update_scene_rect()
rect2 = canvas2.scene.sceneRect()
print(
    "Scene rect after direct add:",
    rect2.left(),
    rect2.right(),
    rect2.top(),
    rect2.bottom(),
)
print("Contains node?", rect2.contains(ni_item.pos()))

print("Done")
