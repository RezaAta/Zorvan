"""
Dialog for editing node properties.
"""

import ast
import inspect

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)


class NodeEditorDialog:
    """Adapter-style NodeEditorDialog. Use MVVM implementation via `gui_framework`."""

    def __init__(self, node, parent=None):
        # Delegate to MVVM implementation at runtime
        try:
            from gui_framework.viewmodels.node_editor_viewmodel import (
                NodeEditorViewModel,
            )
            from gui_framework.views.node_editor_dialog import (
                NodeEditorDialog as MVVMNodeEditorDialog,
            )
        except Exception as e:
            raise ImportError("MVVM NodeEditor components not available: " + str(e))

        # Construct VM and load node into it
        self._vm = NodeEditorViewModel(node)
        try:
            self._vm.initialize()
        except Exception:
            pass

        self._dlg = MVVMNodeEditorDialog(self._vm, parent)

        self.node = node

    def exec(self):
        return self._dlg.exec()

    def close(self):
        return self._dlg.close()

    def __getattr__(self, name):
        return getattr(self._dlg, name)

    # Legacy implementation removed — MVVM adapter is used instead.
    # All legacy UI and logic has been replaced by the MVVM-based dialog.
    pass

    # Legacy implementation removed — handled by MVVM dialog in gui_framework.
    # Leaving minimal placeholder to keep module importable in rare fallback cases.
    def on_regenerate_population(self):
        pass

    def on_show_population_stats(self):
        pass

    def on_reinitialize_weight(self):
        pass

    def update_node_parameters_from_widgets(self):
        pass

    def create_widget_for_parameter(self, param_name, current_value, param):
        raise NotImplementedError("Legacy UI removed — use MVVM dialog instead")

    def save_changes(self):
        raise NotImplementedError("Legacy UI removed — use MVVM dialog instead")


# NodeEditorDialog migrated to MVVM (gui_framework). The legacy UI code has
# been removed. This module provides `NodeEditorDialog(node, parent)` which
# delegates to the MVVM implementation in `gui_framework`.
