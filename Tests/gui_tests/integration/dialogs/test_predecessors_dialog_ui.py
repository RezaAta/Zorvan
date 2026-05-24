import pytest

# Skip GUI tests when PyQt6 isn't available in CI environments
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow, PredecessorsDialog
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.DataStreamNode import DataStreamNode
from zorvan.Nodes.DisplayNode import DisplayNode


def test_predecessors_dialog_layout():
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication([])
        owns_app = True
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
    dlg.show()
    app.processEvents()
    assert dlg.minimumWidth() >= 320
    assert dlg.list_widget.count() == 1
    item = dlg.list_widget.item(0)
    assert item.text() == "disp1"
    dlg.close()
    if owns_app:
        app.quit()
