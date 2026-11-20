"""Learning Rate dialog (MVVM) - small editor for a learning rate node."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QVBoxLayout,
)

from ...viewmodels.dialogs.learning_rate_viewmodel import LearningRateViewModel
from ..base import BaseView


class LearningRateDialog(QDialog, BaseView):
    def __init__(self, vm: LearningRateViewModel, parent=None):
        QDialog.__init__(self, parent)
        BaseView.__init__(self, vm, parent)
        self._vm = vm
        self.setWindowTitle("Learning Rate")
        self.setMinimumWidth(320)

        self._setup_ui()
        try:
            self.get_viewmodel().initialize()
        except Exception:
            pass
        try:
            self._bind_viewmodel()
        except Exception:
            pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(1e-6, 10.0)
        self.lr_spin.setDecimals(6)
        self.lr_spin.setSingleStep(0.001)
        self.lr_spin.setValue(self.get_viewmodel().get_value())
        form.addRow("Learning rate:", self.lr_spin)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _bind_viewmodel(self):
        vm = self.get_viewmodel()

        # VM -> UI
        try:
            vm.observe_property("value", lambda o, n: self.lr_spin.setValue(float(n)))
        except Exception:
            pass

        # UI -> VM
        try:
            self.lr_spin.valueChanged.connect(lambda v: vm.set_value(float(v)))
        except Exception:
            pass

    def _on_accept(self):
        # Ensure last value pushed
        try:
            self.get_viewmodel().set_value(self.lr_spin.value())
        except Exception:
            pass
        self.accept()

    def apply_to_node(self, node):
        return self.get_viewmodel().apply_to_node(node)

    def get_value(self):
        return self.get_viewmodel().get_value()
