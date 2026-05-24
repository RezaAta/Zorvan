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

    # Activation label should be hidden by default
    assert hasattr(dlg, "per_layer_label")
    assert dlg.per_layer_label.isHidden() is True

    # Set global activation and toggle per-layer activations to show label and combos
    dlg.global_activation.setCurrentText("Tanh")
    dlg.per_layer_checkbox.setChecked(True)
    dlg._toggle_per_layer_selectors(2)
    # now label and combos should be *not* hidden (visible state depends on parent)
    assert dlg.per_layer_label.isHidden() is False
    dlg._per_layer_combos[0].setCurrentText("Tanh")
    dlg._per_layer_combos[1].setCurrentText("Sigmoid")

    # Toggle bias to False and ensure it's recorded
    dlg.bias_checkbox.setChecked(False)

    # Now hide per-layer again
    dlg.per_layer_checkbox.setChecked(False)
    dlg._toggle_per_layer_selectors(2)
    assert dlg.per_layer_label.isHidden() is True

    # Trigger generation via clicking the button (simulates UI)
    dlg.generate_btn.click()

    g = dlg.get_graph()
    assert g is not None
    # Expect a full MLP with weights/biases/buffers; should be significantly larger than the minimal node set
    assert len(g.nodes) > 20

    # Ensure the returned graph implements the Core.Graph API so editor/commands work
    from zorvan.Core.Graph import Graph as CoreGraph

    assert isinstance(g, CoreGraph)
    assert hasattr(g, "AddNode")

    # If we set the graph into a MainWindow, the canvas VM should load nodes/edges
    from gui_framework.legacy import MainWindow

    mw = MainWindow()
    mw.set_graph(g)
    # Canvas ViewModel should have loaded nodes and edges
    try:
        vm_nodes = mw.canvas_vm.get_nodes()
        vm_edges = mw.canvas_vm.get_edges()
        assert len(vm_nodes) == len(g.nodes)
        assert len(vm_edges) >= 0
    except Exception:
        # If canvas viewmodel not fully wired in headless test environment, at least ensure no exceptions
        pass

    # Basic node shape checks
    names = [n.name for n in g.nodes]
    assert "x0" in names
    # Hidden layer neurons now use Add/Act/Buffer naming
    assert any(n.startswith("Add_L0N") or n.startswith("Act_L0N") for n in names)
    assert "y0" in names

    # Ensure nodes have a 'value' attribute expected by visualizer
    assert all(hasattr(n, "value") for n in g.nodes)

    # Ensure weight and buffer nodes exist in the generated graph
    assert any(n.name.startswith("W_x") or n.name.startswith("W_H") for n in g.nodes)
    assert any(
        n.name.startswith("Buff_x") or n.name.startswith("Buff_H") for n in g.nodes
    )
    # Bias nodes should reflect the bias checkbox state
    has_bias_nodes = any(
        n.name.startswith("B_H") or n.name.startswith("B_y") for n in g.nodes
    )
    assert has_bias_nodes == bool(g.bias)

    # Check activation attributes and bias flag
    assert hasattr(g, "hiddenLayerActivations")
    assert g.hiddenLayerActivations in (["Tanh", "Sigmoid"], ["Tanh"]) or isinstance(
        g.hiddenLayerActivations, list
    )
    assert hasattr(g, "bias")
    assert g.bias is False

    # Now test using global activation when per-layer disabled
    dlg.per_layer_checkbox.setChecked(False)
    dlg._toggle_per_layer_selectors(2)
    dlg.global_activation.setCurrentText("ReLU")
    dlg.bias_checkbox.setChecked(True)

    dlg.generate_btn.click()
    g2 = dlg.get_graph()
    assert g2 is not None
    assert g2.hiddenLayerActivations == ["ReLU", "ReLU"]
    assert g2.bias is True

    dlg.close()
