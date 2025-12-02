import sys

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode


def test_gui_forward_rewire_buffer():
    app = QApplication(sys.argv)
    window = MainWindow()
    g = window.graph
    # Setup nodes
    ds = DataStreamNode(name="ds", data=[5, 6, 7])
    disp = DisplayNode(name="disp")
    disp.value = 999
    buff = BufferNode(name="b", size=3)
    g.AddNode(ds, disp, buff)

    # Add node items to canvas
    ds_item = window.canvas.add_node_item(ds, x=0, y=0)
    disp_item = window.canvas.add_node_item(disp, x=200, y=0)
    buff_item = window.canvas.add_node_item(buff, x=400, y=0)

    # Connect display -> buffer via canvas
    edge = window.canvas.add_edge_item(disp, buff)

    # Set runner to forward processing to exercise caches
    window.graph_runner.set_graph(g)
    window.graph_runner.processor_type = "forward"
    # Call processing for a few iterations
    window.graph_runner.graph_processor.ForwardProcessing(iterations=4)
    # Buffer should have display value in its buffer
    assert 999 in buff.buffer

    # Now disconnect via PredecessorsDialog
    from ComputationalGraphs.GUI.predecessors_dialog import PredecessorsDialog

    dlg = PredecessorsDialog(buff_item, window.canvas)
    # Find the predecessor(s) and remove the first one
    preds = list(buff.predecessors)
    if preds:
        dlg.disconnect_pred(preds[0])

    # Rewire to data stream
    e2 = window.canvas.add_edge_item(ds, buff)

    # Reset forward state (MainWindow.on_edge_removed should have triggered this, but ensure here)
    if window.graph_runner.graph_processor:
        try:
            window.graph_runner.graph_processor.reset_forward_state()
        except Exception:
            pass

    window.graph_runner.graph_processor.ForwardProcessing(iterations=4)
    # Now buffer should contain data stream values (5,6 or 7)
    assert buff.buffer[-1] in (5, 6, 7)

    app.quit()
