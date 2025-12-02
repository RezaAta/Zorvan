import sys

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode

app = QApplication(sys.argv)
win = MainWindow()

# Add nodes visually
x = DataStreamNode(name="x", data=[1, 2, 3])
b = BufferNode(name="b", size=3)

win.canvas.add_node_item(x, 0, 0)
win.canvas.add_node_item(b, 200, 0)
# Rebuild underlying graph
win.rebuild_graph()

# Connect and then remove
edge = win.canvas.add_edge_item(x, b)
print("Before remove:", x in b.predecessors)
edge.setSelected(True)
win.canvas.remove_selected_items()
print("After remove:", x in b.predecessors)

app.quit()
