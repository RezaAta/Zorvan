import sys

from PyQt6.QtWidgets import QApplication

from zorvan.GUI.main_window import MainWindow
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.DisplayNode import DisplayNode

app = QApplication(sys.argv)
window = MainWindow()
g = window.graph

# nodes
disp = DisplayNode(name="disp")
buff = BufferNode(name="b", size=2)
g.AddNode(disp, buff)

disp_item = window.canvas.add_node_item(disp, x=200, y=0)
buff_item = window.canvas.add_node_item(buff, x=400, y=0)
edge = window.canvas.add_edge_item(disp, buff)
print("before: buff.predecessors =", buff.predecessors)
from zorvan.GUI.predecessors_dialog import PredecessorsDialog

dlg = PredecessorsDialog(buff_item, window.canvas)
print("dlg count init =", dlg.list_widget.count())
# remove edge
edge.setSelected(True)
window.canvas.remove_selected_items()
print("after: buff.predecessors =", buff.predecessors)
print("dlg count after =", dlg.list_widget.count())
input("done")
