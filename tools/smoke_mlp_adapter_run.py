import os
import sys

from PyQt6.QtWidgets import QApplication

# ensure repo root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from zorvan.GUI.mlp_dialog import MLPGeneratorDialog

app = QApplication.instance() or QApplication([])
dlg = MLPGeneratorDialog()
# Configure via legacy-style API
dlg.num_hidden_layers.setValue(2)
dlg._update_hidden_layer_sizes(2)
# try per-layer
dlg.per_layer_checkbox.setChecked(True)
dlg._toggle_per_layer_selectors(2)
# set per-layer activations
per_layer_controls = getattr(dlg, "per_layer_selectors", None)
if per_layer_controls is None:
    per_layer_controls = getattr(dlg._dlg, "_per_layer_combos", [])
if len(per_layer_controls) >= 2:
    per_layer_controls[0].setCurrentText("Tanh")
    per_layer_controls[1].setCurrentText("Sigmoid")
# toggle bias
try:
    dlg.bias_checkbox.setChecked(True)
except Exception:
    pass

# Generate
try:
    dlg._generate_mlp()
    g = dlg.get_graph()
    print("Generated graph:", g)
    if g is not None:
        print("hiddenLayerSizes =", getattr(g, "hiddenLayerSizes", None))
        print("hiddenLayerActivations =", getattr(g, "hiddenLayerActivations", None))
        print(
            "hiddenActivationFunctions =",
            (
                [c.__name__ for c in getattr(g, "hiddenActivationFunctions", [])]
                if hasattr(g, "hiddenActivationFunctions")
                else None
            ),
        )
except Exception as e:
    print("Error during generation:", e)

print("Done")
