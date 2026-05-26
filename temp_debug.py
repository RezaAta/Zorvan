from PyQt6.QtWidgets import QApplication
from gui_framework.legacy import MainWindow

app = QApplication([])
mw = MainWindow()
canvas = mw.canvas
node = canvas._create_node_by_class_name('AdditionNode', {'name': 'AddTest'})
node_item = canvas.add_node_item(node, x=50, y=50)
print('initial node_item', id(node_item), id(node_item.value_label))
print('canvas node item', id(canvas.node_items[node]))
print('graph nodes', [n.name for n in mw.graph.nodes])
print('node in graph', node in mw.graph.nodes)
mw.execution_controller.play()
app.processEvents()
print('after play current_step', mw.execution_controller.graph_runner.current_step)
print('same node_item?', canvas.node_items[node] is node_item)
import traceback
try:
    print('value_label exists', id(node_item.value_label), node_item.value_label.toPlainText())
except Exception as e:
    print('value_label error', repr(e))
    traceback.print_exc()
