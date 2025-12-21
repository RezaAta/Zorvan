"""
Integration tests for new MLPGeneratorDialog in MVVM UI.
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
    from gui_framework.views.dialogs.mlp_generator_dialog import MLPGeneratorDialog


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_mlp_generator_dialog_creates_graph(qapp):
    dlg = MLPGeneratorDialog()

    dlg.num_inputs.setValue(3)
    dlg.num_hidden_layers.setValue(2)
    # Update hidden sizes to ensure widgets created
    dlg._update_hidden_sizes(2)
    dlg._hidden_spinboxes[0].setValue(4)
    dlg._hidden_spinboxes[1].setValue(2)
    dlg.num_outputs.setValue(1)

    # Trigger generation
    dlg._on_generate()

    g = dlg.get_graph()
    assert g is not None
    # Expected node count: 3 inputs + 4 + 2 hidden + 1 output = 10
    assert len(g.nodes) == 10

    # Basic node shape checks
    names = [n.name for n in g.nodes]
    assert "x0" in names
    assert "H0N0" in names
    assert "y0" in names

    dlg.close()
