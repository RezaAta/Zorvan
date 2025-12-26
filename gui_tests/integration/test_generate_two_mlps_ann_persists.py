"""
Integration test to reproduce the report: generate MLP twice and ensure ANN colors
remain applied to the second generated graph.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from ComputationalGraphs.GUI.main_window import MainWindow
    from gui_framework.viewmodels.mlp_generator_viewmodel import MLPGeneratorViewModel


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_generate_multiple_mlps_ann_colors_persist(qapp):
    mw = MainWindow()

    gen = MLPGeneratorViewModel()
    g1 = gen.generate(num_inputs=2, hidden_layers=[2], num_outputs=1)

    # Simulate first generate flow
    mw.canvas.scene.clear()
    mw.canvas.node_items.clear()
    mw.set_graph(g1)
    mw._visualize_graph_on_canvas(g1)
    # Layout call should enable ANN and apply colors
    mw.apply_graph_layout("mlp_layout", spacing=80)

    # Ensure ANN turned on and colors applied for first graph
    assert getattr(mw, "ann_colors_enabled", False) is True
    assert getattr(mw.canvas, "ann_colors_active", False) is True
    assert any(
        getattr(ni, "manual_color", None) is not None
        for ni in mw.canvas.node_items.values()
    )

    # Now generate second MLP and replace graph
    g2 = gen.generate(num_inputs=3, hidden_layers=[3], num_outputs=1)
    mw.canvas.scene.clear()
    mw.canvas.node_items.clear()
    mw.set_graph(g2)
    mw._visualize_graph_on_canvas(g2)
    mw.apply_graph_layout("mlp_layout", spacing=80)

    # ANN should remain enabled and the new nodes should have ANN manual color set
    assert getattr(mw, "ann_colors_enabled", False) is True
    assert getattr(mw.canvas, "ann_colors_active", False) is True
    assert any(
        getattr(ni, "manual_color", None) is not None
        for ni in mw.canvas.node_items.values()
    )
