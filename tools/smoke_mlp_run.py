import os
import sys

from PyQt6.QtWidgets import QApplication

# Ensure repo root is on sys.path for direct script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gui_framework.views.dialogs.mlp_generator_dialog import MLPGeneratorDialog

app = QApplication.instance() or QApplication([])
dlg = MLPGeneratorDialog()
# simple smoke test
dlg.num_inputs.setValue(2)
dlg.num_hidden_layers.setValue(2)
dlg._update_hidden_sizes(2)
dlg._hidden_spinboxes[0].setValue(3)
dlg._hidden_spinboxes[1].setValue(4)
dlg.global_activation.setCurrentText("Tanh")
dlg.per_layer_checkbox.setChecked(True)
dlg._toggle_per_layer_selectors(2)
dlg._per_layer_combos[0].setCurrentText("Tanh")
dlg._per_layer_combos[1].setCurrentText("Sigmoid")
dlg.bias_checkbox.setChecked(True)
dlg._on_generate()
g = dlg.get_graph()
print(
    "Graph attrs:",
    getattr(g, "hiddenLayerSizes", None),
    getattr(g, "hiddenLayerActivations", None),
    getattr(g, "bias", None),
)
assert g is not None
print("Smoke run OK")
