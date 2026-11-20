import json
import os
import tempfile

import numpy as np
import pytest

from gui_framework.legacy import ExamplesLoader
from zorvan_reference.Core.CGJsonIO import load, save
from zorvan_reference.Core.Graph import Graph

# Skip GUI tests when PyQt6 isn't available in the environment
pytest.importorskip("PyQt6")

from gui_framework.legacy import MainWindow


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
    from zorvan_reference.Nodes.DisplayNode import DisplayNode
    from zorvan_reference.Nodes.PiecewiseLinearNode import PiecewiseLinearNode

    # Small fuzzy-style graph: input -> piecewise membership with numpy arrays
    ex = Graph()
    inp = DisplayNode(name="input", value=10.0)
    member = PiecewiseLinearNode(name="member")
    member.xs = np.array([0.0, 25.0, 50.0])
    member.mus = np.array([0.0, 0.5, 1.0])
    ex.AddNode(inp, member)
    ex.ConnectPreNode(member, inp)

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
