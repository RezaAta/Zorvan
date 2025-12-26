import os
import sys

from PyQt6.QtWidgets import QApplication

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ComputationalGraphs.GUI.mlp_dialog import MLPGeneratorDialog

app = QApplication.instance() or QApplication([])

# Create dialog and generate graph
dlg = MLPGeneratorDialog()
# Use MVVM path
try:
    dlg.num_inputs.setValue(3)
    dlg.num_hidden_layers.setValue(2)
    dlg._update_hidden_layer_sizes(2)
    dlg._hidden_spinboxes[0].setValue(3)
    dlg._hidden_spinboxes[1].setValue(2)
    dlg.per_layer_checkbox.setChecked(True)
    dlg._toggle_per_layer_selectors(2)
    dlg._per_layer_combos[0].setCurrentText("Tanh")
    dlg._per_layer_combos[1].setCurrentText("Sigmoid")
    dlg.bias_checkbox.setChecked(True)
    dlg._on_generate()
except Exception as e:
    print("Error generating:", e)

g = dlg.get_graph()
print("Generated graph type:", type(g))
print("Generated graph node count:", len(getattr(g, "nodes", [])))
print("Node names:", [n.name for n in getattr(g, "nodes", [])])

# Try visualize using GraphBuilderController
from ComputationalGraphs.GUI.controllers.graph_builder_controller import (
    GraphBuilderController,
)
from ComputationalGraphs.GUI.main_window import MainWindow

mw = MainWindow()
controller = GraphBuilderController(mw)
try:
    mw.set_graph(g)
    # Now visualize
    controller.visualize_graph_on_canvas(g)
    print("Visualization succeeded")
except Exception as e:
    print("Visualization failed:", e)

print("Done")
