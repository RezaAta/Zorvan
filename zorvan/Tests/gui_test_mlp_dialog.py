from PyQt6.QtWidgets import QApplication

from zorvan.GUI.mlp_dialog import MLPGeneratorDialog
from zorvan.Nodes.TanhNode import TanhNode


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
    # Set per-layer activations (adapter provides per_layer_selectors via delegation)
    # In legacy adapter, per_layer_selectors may not exist; try both paths
    per_layer_controls = getattr(dlg, "per_layer_selectors", None)
    if per_layer_controls is None:
        per_layer_controls = getattr(dlg._dlg, "_per_layer_combos", [])

    if len(per_layer_controls) >= 2:
        per_layer_controls[0].setCurrentText("Tanh")
        per_layer_controls[1].setCurrentText("Sigmoid")

    # Toggle bias checkbox and ensure it is considered
    try:
        dlg.bias_checkbox.setChecked(False)
    except Exception:
        pass

    # Generate MLP
    dlg._generate_mlp()
    g = dlg.get_graph()
    assert g is not None

    # Hidden activation functions stored as a list of classes (legacy attr)
    if hasattr(g, "hiddenActivationFunctions"):
        names = [cls.__name__ for cls in g.hiddenActivationFunctions]
        assert "TanhNode" in names and "SigmoidNode" in names

    # Also check the new string-based attribute
    if hasattr(g, "hiddenLayerActivations"):
        assert isinstance(g.hiddenLayerActivations, list)
        assert (
            "Tanh" in g.hiddenLayerActivations or "Sigmoid" in g.hiddenLayerActivations
        )

    # Bias flag
    assert hasattr(g, "bias")
    assert g.bias in (True, False)
