import sys
from PyQt6.QtWidgets import QApplication
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.GUI.replace_node_dialog import ReplaceNodeDialog
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
from ComputationalGraphs.GUI.graph_canvas import GraphCanvas
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.GUI.main_window import MainWindow

def test_graph_canvas_connect_disconnect():
    app = QApplication(sys.argv)
    g = Graph()
    ds = DataStreamNode(name='ds', data=[10,20,30])
    disp = DisplayNode(name='disp')
    disp.value = 42
    buff = BufferNode(name='b', size=3)
    g.AddNode(ds, disp, buff)

    canvas = GraphCanvas()
    canvas.graph = g
    # attach node items
    ds_item = canvas.add_node_item(ds, x=0, y=0)
    disp_item = canvas.add_node_item(disp, x=200, y=0)
    buff_item = canvas.add_node_item(buff, x=400, y=0)

    # Connect disp -> buff via canvas (should call graph.ConnectPreNode)
    edge_item = canvas.add_edge_item(disp, buff)
    assert disp in buff.predecessors

    # Now disconnect using canvas remove functionality
    edge_item.setSelected(True)
    canvas.remove_selected_items()
    # After removal, disp should no longer be in buff.predecessors
    assert disp not in buff.predecessors

    # Now add ds -> buff
    edge_item2 = canvas.add_edge_item(ds, buff)
    assert ds in buff.predecessors

    # Clean up
    app.quit()


def test_gui_rewire_buffer_after_replace():
    app = QApplication(sys.argv)
    g = Graph()
    # data stream has values [5,6,7]
    ds = DataStreamNode(name='ds', data=[5,6,7])
    disp = DisplayNode(name='disp')
    disp.value = 999
    buff = BufferNode(name='b', size=3)
    g.AddNode(ds, disp, buff)

    canvas = GraphCanvas()
    canvas.graph = g
    ds_item = canvas.add_node_item(ds, x=0, y=0)
    disp_item = canvas.add_node_item(disp, x=200, y=0)
    buff_item = canvas.add_node_item(buff, x=400, y=0)

    # Step 1: connect display -> buff and run
    e1 = canvas.add_edge_item(disp, buff)
    proc = GraphProcessor(g, auto_threading=False)
    proc.ComputeGraph(2)
    # buffer should include display value 999
    assert 999 in buff.buffer

    # Step 2: disconnect display edge and connect data stream edge
    e1.setSelected(True)
    canvas.remove_selected_items()
    e2 = canvas.add_edge_item(ds, buff)
    proc.time = 0
    proc.ComputeGraph(3)
    # Now ensure the most recently appended value is a data stream value
    assert buff.buffer[-1] in (5, 6, 7)

    # Clean up
    app.quit()


def test_predecessors_dialog_disconnect():
    app = QApplication(sys.argv)
    window = MainWindow()
    g = window.graph
    ds = DataStreamNode(name='ds', data=[1,2,3])
    disp = DisplayNode(name='disp')
    disp.value = 42
    buff = BufferNode(name='b', size=2)
    g.AddNode(ds, disp, buff)

    ds_item = window.canvas.add_node_item(ds, x=0, y=0)
    disp_item = window.canvas.add_node_item(disp, x=200, y=0)
    buff_item = window.canvas.add_node_item(buff, x=400, y=0)

    # Connect display -> buff
    window.canvas.add_edge_item(disp, buff)
    assert disp in buff.predecessors

    # Open predecessors dialog and disconnect
    from ComputationalGraphs.GUI.predecessors_dialog import PredecessorsDialog
    dlg = PredecessorsDialog(buff_item, window.canvas)
    dlg.disconnect_pred(disp)
    # Pred list must update
    assert disp not in buff.predecessors

    app.quit()


def test_predecessors_dialog_updates_on_external_delete():
    app = QApplication(sys.argv)
    window = MainWindow()
    g = window.graph
    # nodes
    disp = DisplayNode(name='disp')
    buff = BufferNode(name='b', size=2)
    g.AddNode(disp, buff)

    disp_item = window.canvas.add_node_item(disp, x=200, y=0)
    buff_item = window.canvas.add_node_item(buff, x=400, y=0)
    edge = window.canvas.add_edge_item(disp, buff)

    assert disp in buff.predecessors
    from ComputationalGraphs.GUI.predecessors_dialog import PredecessorsDialog
    dlg = PredecessorsDialog(buff_item, window.canvas)
    # Initially, should have one predecessor
    assert dlg.list_widget.count() == 1

    # Now remove edge via canvas remove method (simulate Delete)
    edge.setSelected(True)
    window.canvas.remove_selected_items()

    # Dialog should have updated automatically
    assert disp not in buff.predecessors
    assert dlg.list_widget.count() == 0
    app.quit()


def test_predecessors_dialog_disconnect():
    app = QApplication(sys.argv)
    g = Graph()
    ds = DataStreamNode(name='ds', data=[1,2,3])
    disp = DisplayNode(name='disp')
    disp.value = 88
    buff = BufferNode(name='b', size=3)
    g.AddNode(ds, disp, buff)

    canvas = GraphCanvas()
    canvas.graph = g
    ds_item = canvas.add_node_item(ds, x=0, y=0)
    disp_item = canvas.add_node_item(disp, x=200, y=0)
    buff_item = canvas.add_node_item(buff, x=400, y=0)

    # Connect display -> buffer
    canvas.add_edge_item(disp, buff)
    assert disp in buff.predecessors

    # Open predecessors dialog and disconnect disp programmatically
    from ComputationalGraphs.GUI.predecessors_dialog import PredecessorsDialog
    dlg = PredecessorsDialog(buff_item, canvas)
    dlg.disconnect_pred(disp)
    assert disp not in buff.predecessors

    app.quit()


def test_rebuild_graph_syncs_canvas_and_graph():
    """Test that rebuild_graph results in the canvas.graph being synchronized with window.graph
    and that connect/disconnect operations apply to the authoritative graph object.
    """
    app = QApplication(sys.argv)
    window = MainWindow()

    # Create nodes that haven't been added to the window.graph
    ds = DataStreamNode(name='ds', data=[1, 2, 3])
    buff = BufferNode(name='b', size=2)

    # Add nodes visually to canvas only
    ds_item = window.canvas.add_node_item(ds, x=0, y=0)
    buff_item = window.canvas.add_node_item(buff, x=200, y=0)

    # Rebuild the underlying graph from canvas; this should set window.graph via set_graph
    window.rebuild_graph()

    # The canvas.graph should now be the same as window.graph (synchronized by set_graph)
    assert getattr(window.canvas, 'graph', None) is window.graph

    # Create an edge visually and ensure the authoritative graph reflects it
    edge = window.canvas.add_edge_item(ds, buff)
    assert ds in buff.predecessors

    # Now disconnect using the canvas and ensure model updated
    edge.setSelected(True)
    window.canvas.remove_selected_items()
    assert ds not in buff.predecessors

    app.quit()


def test_graph_canvas_replace_node_item():
    app = QApplication(sys.argv)
    g = Graph()
    ds = DataStreamNode(name='ds', data=[1, 2, 3])
    add = AdditionNode(name='add')
    mul = MultiplicationNode(name='mul')
    g.AddNode(ds, add, mul)
    # connect ds -> add -> mul
    g.ConnectPreNode(add, ds)
    g.ConnectPreNode(mul, add)

    canvas = GraphCanvas()
    canvas.graph = g
    ds_item = canvas.add_node_item(ds, x=0, y=0)
    add_item = canvas.add_node_item(add, x=200, y=0)
    mul_item = canvas.add_node_item(mul, x=400, y=0)

    # Replace add node with a multiplication node
    new_node = canvas.replace_node_item(add_item, 'MultiplicationNode')
    assert new_node is not None
    assert new_node in g.nodes
    assert add not in g.nodes
    # NodeItem of the original should now refer to new_node
    assert add_item.node is new_node
    # Predecessor relationships should remain
    assert ds in new_node.predecessors
    assert any(pred is new_node for pred in mul.predecessors)
    app.quit()


def test_replace_dialog_search_does_not_crash():
    app = QApplication(sys.argv)
    # Construct dialog and simulate typing
    dlg = ReplaceNodeDialog()
    # Set a search text to activate filtering
    dlg.search_bar.setText('mul')
    # Ensure selected_type remains None if nothing selected
    assert dlg.selected_type() is None
    app.quit()
