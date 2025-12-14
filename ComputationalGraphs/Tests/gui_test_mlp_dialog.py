from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.mlp_dialog import MLPGeneratorDialog
from ComputationalGraphs.Nodes.TanhNode import TanhNode


def test_mlp_dialog_has_tanh_mapping():
    app = QApplication.instance() or QApplication([])
    dlg = MLPGeneratorDialog()
    cls = dlg._get_activation_class("Tanh")
    assert cls is TanhNode


def test_mlp_dialog_per_layer_generation():
    app = QApplication.instance() or QApplication([])
    dlg = MLPGeneratorDialog()
    # Configure two hidden layers
    dlg.num_hidden_layers.setValue(2)
    dlg._update_hidden_layer_sizes(2)
    # Enable per-layer selectors and set them
    dlg.per_layer_checkbox.setChecked(True)
    dlg._toggle_per_layer_selectors(2)
    # Set per-layer activations
    if len(dlg.per_layer_selectors) >= 2:
        dlg.per_layer_selectors[0].setCurrentText("Tanh")
        dlg.per_layer_selectors[1].setCurrentText("Sigmoid")
    # Generate MLP
    dlg._generate_mlp()
    g = dlg.get_graph()
    assert g is not None
    # Hidden activation functions stored as a list
    if hasattr(g, "hiddenActivationFunctions"):
        names = [cls.__name__ for cls in g.hiddenActivationFunctions]
        assert "TanhNode" in names and "SigmoidNode" in names
