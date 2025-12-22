"""Dialog for generating MLP graphs."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.ReLUNode import ReLUNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
from ComputationalGraphs.Nodes.TanhNode import TanhNode

"""
Thin adapter that exposes the MVVM `MLPGeneratorDialog` under the legacy import path.
This keeps existing code that imports `ComputationalGraphs.GUI.MLPGeneratorDialog` working
while we migrate to the MVVM implementation in `gui_framework.views.dialogs`.
"""

try:
    from gui_framework.views.dialogs.mlp_generator_dialog import (
        MLPGeneratorDialog as MVVMMlpDialog,
    )
except Exception as e:
    raise ImportError("MVVM MLPGeneratorDialog not available: " + str(e))


class MLPGeneratorDialog:
    """Legacy-compatible adapter around the MVVM dialog."""

    def __init__(self, parent=None):
        self._dlg = MVVMMlpDialog(parent)

    def exec(self):
        return self._dlg.exec()

    def get_graph(self):
        return self._dlg.get_graph()

    def close(self):
        return self._dlg.close()

    def __getattr__(self, name):
        return getattr(self._dlg, name)
