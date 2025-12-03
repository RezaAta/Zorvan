import sys
import time

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.BufferNode import BufferNode


def test_resume_rebuild_after_pause():
    app = QApplication(sys.argv)
    window = MainWindow()
    g = window.graph

    # Setup initial nodes and graph
    ds = DataStreamNode(name="ds", data=[1, 2, 3])
    disp = DisplayNode(name="disp")
    disp.value = 123
    g.AddNode(ds, disp)

    # Add them to canvas and connect them
    window.canvas.add_node_item(ds, x=0, y=0)
    window.canvas.add_node_item(disp, x=200, y=0)

    window.canvas.add_edge_item(ds, disp)

    # Rebuild graph to ensure authoritative graph includes items
    window.rebuild_graph()

    # Run graph for a couple of steps and then pause
    window.play_graph()
    # Wait so that at least one iteration runs
    time.sleep(0.2)
    window.pause_graph()
    time.sleep(0.05)

    # Add a new buffer node to the canvas while paused
    buff2 = BufferNode(name="b2", size=3)
    window.canvas.add_node_item(buff2, x=400, y=0)
    # Connect disp -> buff2 (new node is only on canvas now)
    window.canvas.add_edge_item(disp, buff2)

    # Rebuild authoritative graph from canvas to include new node
    window.rebuild_graph()

    # Resume and allow more iterations
    window.resume_graph()
    # Give time for the resumed worker to process and update buffer
    time.sleep(0.25)

    # Confirm that the new buffer node was processed after resume
    assert hasattr(buff2, "buffer") and len(buff2.buffer) > 0
    assert buff2.buffer[-1] == disp.value

    # Clean up
    window.pause_graph()
    app.quit()
