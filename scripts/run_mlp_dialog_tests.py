import importlib
import os
import sys

from PyQt6.QtWidgets import QApplication

# Ensure repo root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

app = QApplication.instance() or QApplication([])
mod = importlib.import_module("ComputationalGraphs.Tests.gui_test_mlp_dialog")
print("Running tests in", mod.__file__)
mod.test_mlp_dialog_has_tanh_mapping()
print("test_mlp_dialog_has_tanh_mapping passed")
mod.test_mlp_dialog_per_layer_generation()
print("test_mlp_dialog_per_layer_generation passed")
mod2 = importlib.import_module("ComputationalGraphs.Tests.gui_test_mlp_sizes")
mod2.test_mlp_dialog_hidden_layer_sizes()
print("test_mlp_dialog_hidden_layer_sizes passed")
print("All legacy dialog tests passed")
