import sys

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import GraphCanvas
from zorvan.Core.Graph import Graph
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.DataStreamNode import DataStreamNode
from zorvan.Nodes.DisplayNode import DisplayNode

app = QApplication(sys.argv)

# Build graph
g = Graph()
ds = DataStreamNode(name="ds", data=[10, 20, 30])
disp = DisplayNode(name="disp")
buff = BufferNode(name="b", size=3)
g.AddNode(ds, disp, buff)

canvas = GraphCanvas()
canvas.graph = g
# attach node items
ds_item = canvas.add_node_item(ds, x=0, y=0)
disp_item = canvas.add_node_item(disp, x=200, y=0)
buff_item = canvas.add_node_item(buff, x=400, y=0)
edge_item = canvas.add_edge_item(disp, buff)
print("Edge items count before:", len(canvas.edge_items))
# select edge
edge_item.setSelected(True)
print("Selected items:", canvas.scene.selectedItems())
# call remove
canvas.remove_selected_items()
print("Edge items after removal:", len(canvas.edge_items))
print("buff predecessors:", buff.predecessors)
app.quit()
