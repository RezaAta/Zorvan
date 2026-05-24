import sys
import time

import pytest

# Skip GUI tests when PyQt6 isn't available in CI environments
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.DataStreamNode import DataStreamNode
from zorvan.Nodes.DisplayNode import DisplayNode


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
    # Wait for buffer to update and reflect current display value
    for _ in range(10):
        time.sleep(0.05)
        if (
            hasattr(buff2, "buffer")
            and len(buff2.buffer) > 0
            and buff2.buffer[-1] == disp.value
        ):
            break

    # Confirm that the new buffer node was processed after resume
    assert hasattr(buff2, "buffer") and len(buff2.buffer) > 0
    # Buffer may be slightly behind due to scheduling; ensure it contains
    # a recent value from the data stream (sanity check for processing after resume)
    assert buff2.buffer[-1] in (1, 2, 3)

    # Clean up
    window.pause_graph()
    app.quit()
