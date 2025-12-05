import json
import os
import tempfile

import numpy as np
import pytest

from ComputationalGraphs.Core.CGJsonIO import load, save
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.GUI.examples_loader import ExamplesLoader

# Skip GUI tests when PyQt6 isn't available in the environment
pytest.importorskip("PyQt6")

from ComputationalGraphs.GUI.main_window import MainWindow


def test_cgjson_save_load_basic():
    loader = ExamplesLoader()
    fib_graph = loader.categories["basic"].examples[0][2]()
    assert isinstance(fib_graph, Graph)

    # set some visuals manually to emulate GUI
    for idx, node in enumerate(fib_graph.nodes):
        node.gui_pos = (idx * 10.0, idx * 15.0)
        node.gui_color = "#00ff00"
        node.gui_radius = 40

    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".cgjson")
    tmpname = tmpf.name
    tmpf.close()
    try:
        save(fib_graph, tmpname, canvas=None, compress=False)
        loaded = load(tmpname)
        assert isinstance(loaded, Graph)
        assert len(loaded.nodes) == len(fib_graph.nodes)
        # verify visuals restored
        for orig, re in zip(fib_graph.nodes, loaded.nodes):
            assert getattr(re, "gui_pos", None) == getattr(orig, "gui_pos", None)
            assert getattr(re, "gui_color", None) == getattr(orig, "gui_color", None)
    finally:
        try:
            os.remove(tmpname)
        except OSError:
            pass


def test_cgjson_save_load_numpy_attrs():
    loader = ExamplesLoader()
    # Use piecewise node from fuzzy systems
    ex = loader.categories["fuzzy_systems"].examples[0][2]()
    # Find any PiecewiseLinearNode and set numpy arrays explicitly
    found = False
    for n in ex.nodes:
        if (
            type(getattr(n, "__class__", None)).__name__ == "PiecewiseLinearNode"
            or n.__class__.__name__ == "PiecewiseLinearNode"
        ):
            n.xs = np.array([0.0, 25.0, 50.0])
            n.mus = np.array([0.0, 0.5, 1.0])
            found = True
            break
    if not found:
        # fallback to simple graph
        ex = loader.categories["basic"].examples[0][2]()

    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".cgjson")
    tmpname = tmpf.name
    tmpf.close()
    try:
        save(ex, tmpname, canvas=None, compress=False)
        loaded = load(tmpname)
        # Validate that at least number of nodes preserved
        assert len(loaded.nodes) == len(ex.nodes)
        # Check array attribute types for piecewise node
        for o, l in zip(ex.nodes, loaded.nodes):
            if o.__class__.__name__ == "PiecewiseLinearNode":
                assert isinstance(l.xs, np.ndarray)
                assert isinstance(l.mus, np.ndarray)
    finally:
        try:
            os.remove(tmpname)
        except OSError:
            pass


def test_cgjson_save_with_canvas_visuals():
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    loader = ExamplesLoader()
    g = loader.categories["basic"].examples[1][2]()
    # Visualize graph to create NodeItems
    win._visualize_graph_on_canvas(g)

    # Save with canvas visuals
    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".cgjson")
    tmpname = tmpf.name
    tmpf.close()
    try:
        save(g, tmpname, canvas=win.canvas, compress=False)
        loaded = load(tmpname)
        assert isinstance(loaded, Graph)
        # Ensure GUI visuals were serialized as attributes
        for node in loaded.nodes:
            assert hasattr(node, "gui_pos") or hasattr(node, "gui_color")
    finally:
        try:
            os.remove(tmpname)
        except OSError:
            pass


def test_cgjson_save_load_compressed():
    loader = ExamplesLoader()
    fib_graph = loader.categories["basic"].examples[0][2]()
    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".cgz")
    tmpname = tmpf.name
    tmpf.close()
    try:
        save(fib_graph, tmpname, canvas=None, compress=True)
        loaded = load(tmpname)
        assert isinstance(loaded, Graph)
        assert len(loaded.nodes) == len(fib_graph.nodes)
    finally:
        try:
            os.remove(tmpname)
        except OSError:
            pass
