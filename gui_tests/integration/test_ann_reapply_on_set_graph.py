"""
Integration test: verify that ANN colorization is reapplied when a new graph is set while ANN mode is enabled.
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
    from gui_framework.viewmodels.mlp_generator_viewmodel import MLPGeneratorViewModel
    from zorvan.GUI.main_window import MainWindow


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
    # Simulate ANN colorization preference enabled (as if user checked the checkbox)
    mw.ann_colors_enabled = True

    # Set the graph; our change should reapply ANN colors for the new graph
    mw.set_graph(g)

    # Canvas should mark ANN colors as active and node items should have manual colors
    assert getattr(mw.canvas, "ann_colors_active", False) is True
    # At least one node should have manual_color set
    any_manual = any(
        getattr(ni, "manual_color", None) is not None
        for ni in mw.canvas.node_items.values()
    )
    assert any_manual is True
