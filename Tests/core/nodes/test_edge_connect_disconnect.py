from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.DataStreamNode import DataStreamNode
from zorvan.Nodes.DisplayNode import DisplayNode


def test_edge_connect_disconnect_sim():
    g = Graph()
    ds = DataStreamNode(name="ds", data=[10, 20, 30])
    disp = DisplayNode(name="disp")
    disp.value = 42
    buff = BufferNode(name="b", size=3)
    # Add to graph
    g.AddNode(ds, disp, buff)

    # Connect display to buffer (simulate GUI edge creation)
    g.ConnectPreNode(buff, disp)

    proc = GraphProcessor(g, auto_threading=False)
    proc.ComputeGraph(3)
    # After processing we expect buff.buffer to contain display values
    assert 42 in buff.buffer

    # Now disconnect display and connect data stream (simulate user rewire)
    g.DisconnectPreNode(buff, disp)
    g.ConnectPreNode(buff, ds)

    # Reset processor time & run some iterations
    proc.time = 0
    proc.ComputeGraph(3)

    # Now buffer should include data stream values, not display 42
    assert 10 in buff.buffer or 20 in buff.buffer or 30 in buff.buffer
