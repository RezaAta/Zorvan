from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.GUI.predecessors_dialog import PredecessorsDialog
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode


def test_predecessors_dialog_layout():
    app = QApplication([])
    win = MainWindow()
    g = win.graph
    ds = DataStreamNode("ds", data=[1, 2])
    d1 = DisplayNode("disp1")
    b = BufferNode("b")
    g.AddNode(ds, d1, b)
    disp_item = win.canvas.add_node_item(d1, 10, 10)
    buf_item = win.canvas.add_node_item(b, 200, 10)
    edge = win.canvas.add_edge_item(d1, b)
    # Show the dialog
    dlg = PredecessorsDialog(buf_item, win.canvas)
    assert dlg.minimumWidth() >= 360
    assert dlg.list_widget.count() == 1
    # first item size hint should not be tiny
    item = dlg.list_widget.item(0)
    assert item.sizeHint().height() >= 34
    app.quit()
