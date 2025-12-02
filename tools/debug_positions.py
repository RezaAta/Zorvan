import sys

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.examples_loader import ExamplesLoader
from ComputationalGraphs.GUI.main_window import MainWindow

app = QApplication(sys.argv)
loader = ExamplesLoader()
g = loader.categories["basic"].examples[1][2]()
for idx, node in enumerate(g.nodes):
    node.gui_pos = (idx * 30.0, idx * 45.0)
    node.gui_color = "#123456"
    node.gui_radius = 40
win = MainWindow()
win._visualize_graph_on_canvas(g)
for node in g.nodes:
    item = win.canvas.node_items.get(node)
    print(
        node.name, "gui_pos", node.gui_pos, "item_pos", item.pos().x(), item.pos().y()
    )
