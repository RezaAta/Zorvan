"""
Backprop configuration dialog for new UI (collects learning rate and options).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class BackpropConfigDialog(QDialog):
    """Simple dialog to configure backpropagation parameters.

    Accepts an optional ViewModel (BackpropConfigViewModel). When a VM is
    provided the dialog binds controls to it and updates the VM on accept.
    """

    def __init__(self, viewmodel=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Backprop Configuration")
        self.setMinimumWidth(360)
        self._vm = viewmodel
        self._setup_ui()
        self._config = None

        # If a viewmodel was passed, initialize and bind
        if self._vm is not None:
            try:
                self._vm.initialize()
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
        self.lr_spin.setRange(0.00001, 1.0)
        self.lr_spin.setDecimals(5)
        self.lr_spin.setSingleStep(0.001)
        self.lr_spin.setValue(0.01)
        form.addRow("Learning rate:", self.lr_spin)

        self.use_forward_checkbox = QCheckBox(
            "Use forward-processing backprop (no buffers)"
        )
        self.use_forward_checkbox.setChecked(False)
        form.addRow(self.use_forward_checkbox)

        layout.addLayout(form)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_accept(self):
        # If bound to a VM, use it as the canonical source
        self._config = {
            "learning_rate": float(self.lr_spin.value()),
            "use_forward": bool(self.use_forward_checkbox.isChecked()),
        }
        if self._vm is not None:
            try:
                self._vm.set_learning_rate(self._config["learning_rate"])
                self._vm.set_use_forward(self._config["use_forward"])
            except Exception:
                pass
        self.accept()

    def get_config(self):
        return self._config

    def _bind_viewmodel(self):
        """Wire VM <-> UI bindings."""
        vm = self._vm

        # Initialize widgets from VM
        try:
            self.lr_spin.setValue(vm.get_learning_rate())
        except Exception:
            pass
        try:
            self.use_forward_checkbox.setChecked(vm.get_use_forward())
        except Exception:
            pass

        # Observe VM changes and update widgets
        try:
            vm.observe_property(
                "learning_rate", lambda old, new: self.lr_spin.setValue(float(new))
            )
        except Exception:
            pass
        try:
            vm.observe_property(
                "use_forward",
                lambda old, new: self.use_forward_checkbox.setChecked(bool(new)),
            )
        except Exception:
            pass

        # When UI changes, push back to VM (keeping VM as source-of-truth)
        try:
            self.lr_spin.valueChanged.connect(lambda v: vm.set_learning_rate(float(v)))
        except Exception:
            pass
        try:
            self.use_forward_checkbox.stateChanged.connect(
                lambda s: vm.set_use_forward(
                    bool(self.use_forward_checkbox.isChecked())
                )
            )
        except Exception:
            pass

    def closeEvent(self, event):
        event.accept()
