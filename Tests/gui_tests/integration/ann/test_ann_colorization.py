"""Integration tests for ANN colorization behavior."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from gui_framework.viewmodels.mlp_generator_viewmodel import MLPGeneratorViewModel
    from gui_framework.legacy import MainWindow


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_ann_colors_applied_on_set_graph(qapp):
    gen = MLPGeneratorViewModel()
    g = gen.generate(num_inputs=2, hidden_layers=[2], num_outputs=1)

    mw = MainWindow()
    mw.ann_colors_enabled = True
    mw.set_graph(g)

    assert getattr(mw.canvas, "ann_colors_active", False) is True
    any_manual = any(
        getattr(ni, "manual_color", None) is not None
        for ni in mw.canvas.node_items.values()
    )
    assert any_manual is True


def test_generate_multiple_mlps_ann_colors_persist(qapp):
    mw = MainWindow()

    gen = MLPGeneratorViewModel()
    g1 = gen.generate(num_inputs=2, hidden_layers=[2], num_outputs=1)

    mw.canvas.scene.clear()
    mw.canvas.node_items.clear()
    mw.set_graph(g1)
    mw._visualize_graph_on_canvas(g1)
    mw.apply_graph_layout("mlp_layout", spacing=80)

    assert getattr(mw, "ann_colors_enabled", False) is True
    assert getattr(mw.canvas, "ann_colors_active", False) is True
    assert any(
        getattr(ni, "manual_color", None) is not None
        for ni in mw.canvas.node_items.values()
    )

    g2 = gen.generate(num_inputs=3, hidden_layers=[3], num_outputs=1)
    mw.canvas.scene.clear()
    mw.canvas.node_items.clear()
    mw.set_graph(g2)
    mw._visualize_graph_on_canvas(g2)
    mw.apply_graph_layout("mlp_layout", spacing=80)

    assert getattr(mw, "ann_colors_enabled", False) is True
    assert getattr(mw.canvas, "ann_colors_active", False) is True
    assert any(
        getattr(ni, "manual_color", None) is not None
        for ni in mw.canvas.node_items.values()
    )
