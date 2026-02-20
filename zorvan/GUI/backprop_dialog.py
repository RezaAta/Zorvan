"""Dialog for adding backpropagation to existing MLP."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.MLPGraph import MLPGraph

"""Adapter: delegate to MVVM `BackpropDialog` in `gui_framework.views.dialogs`."""

try:
    from gui_framework.viewmodels.dialogs.backprop_viewmodel import BackpropViewModel
    from gui_framework.views.dialogs.backprop_dialog import (
        BackpropDialog as MVVMBackpropDialog,
    )
except Exception as e:
    raise ImportError("MVVM Backprop components not available: " + str(e))


class BackpropDialog:
    """Adapter that exposes the legacy API but delegates to the MVVM implementation."""

    def __init__(self, current_graph, parent=None):
        self._vm = BackpropViewModel(current_graph)
        try:
            self._vm.initialize()
        except Exception:
            pass
        self._dlg = MVVMBackpropDialog(self._vm, parent)
        self.current_graph = current_graph

    def exec(self):
        return self._dlg.exec()

    def get_graph(self):
        return self._dlg.get_graph()

    def close(self):
        return self._dlg.close()

    def __getattr__(self, name):
        return getattr(self._dlg, name)
