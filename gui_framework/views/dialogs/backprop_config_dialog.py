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
    """Simple dialog to configure backpropagation parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Backprop Configuration")
        self.setMinimumWidth(360)
        self._setup_ui()
        self._config = None

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
        self._config = {
            "learning_rate": float(self.lr_spin.value()),
            "use_forward": bool(self.use_forward_checkbox.isChecked()),
        }
        self.accept()

    def get_config(self):
        return self._config

    def closeEvent(self, event):
        event.accept()
