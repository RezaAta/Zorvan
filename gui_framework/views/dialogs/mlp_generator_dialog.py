"""
MLP Generator Dialog (new MVVM view) - minimal dialog that uses
`MLPGeneratorViewModel` to create a simple mock graph for examples/tests.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...viewmodels.mlp_generator_viewmodel import MLPGeneratorViewModel


class MLPGeneratorDialog(QDialog):
    """Dialog that collects MLP dimensions and returns a generated graph object."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Simple MLP (New UI)")
        self.setMinimumWidth(360)
        self._vm = MLPGeneratorViewModel()
        self._vm.initialize()
        self._generated_graph = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.num_inputs = QSpinBox()
        self.num_inputs.setRange(1, 1024)
        self.num_inputs.setValue(2)
        form.addRow("Number of inputs:", self.num_inputs)

        self.num_hidden_layers = QSpinBox()
        self.num_hidden_layers.setRange(0, 8)
        self.num_hidden_layers.setValue(1)
        self.num_hidden_layers.valueChanged.connect(self._update_hidden_sizes)
        form.addRow("Hidden layers:", self.num_hidden_layers)

        # Container for per-layer size inputs
        self.hidden_sizes_widget = QWidget()
        self.hidden_sizes_layout = QVBoxLayout(self.hidden_sizes_widget)
        self.hidden_sizes_layout.setContentsMargins(0, 0, 0, 0)
        form.addRow("Hidden sizes:", self.hidden_sizes_widget)

        self.num_outputs = QSpinBox()
        self.num_outputs.setRange(1, 1024)
        self.num_outputs.setValue(1)
        form.addRow("Number of outputs:", self.num_outputs)

        # Activation options
        self.global_activation = QComboBox()
        self.global_activation.addItems(["Sigmoid", "ReLU", "Tanh", "Linear"])
        self.global_activation.setCurrentText("Sigmoid")
        form.addRow("Hidden activation:", self.global_activation)

        # Output activation selection
        self.output_activation = QComboBox()
        self.output_activation.addItems(["Linear", "Sigmoid", "ReLU", "Tanh"])
        self.output_activation.setCurrentText("Linear")
        form.addRow("Output activation:", self.output_activation)

        self.per_layer_checkbox = QCheckBox("Per-layer activations")
        self.per_layer_checkbox.stateChanged.connect(
            lambda _: self._toggle_per_layer_selectors(self.num_hidden_layers.value())
        )
        form.addRow(self.per_layer_checkbox)

        # Container for per-layer activation selectors (one combobox per hidden layer)
        self.per_layer_selectors_widget = QWidget()
        self.per_layer_selectors_layout = QVBoxLayout(self.per_layer_selectors_widget)
        self.per_layer_selectors_layout.setContentsMargins(0, 0, 0, 0)
        self.per_layer_label = QLabel("Per-layer activations:")
        form.addRow(self.per_layer_label, self.per_layer_selectors_widget)
        # hide label and widget by default
        self.per_layer_label.setVisible(False)
        self.per_layer_selectors_widget.setVisible(False)

        # Bias toggle
        self.bias_checkbox = QCheckBox("Include bias nodes")
        self.bias_checkbox.setChecked(True)
        form.addRow(self.bias_checkbox)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.clicked.connect(self._on_generate)
        button_layout.addWidget(self.generate_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Initialize hidden size controls
        self._hidden_spinboxes = []
        self._per_layer_combos = []
        self._per_layer_combo_rows = []  # Track row widgets for visibility toggle
        self._update_hidden_sizes(self.num_hidden_layers.value())
        # Per-layer selectors hidden by default
        self._toggle_per_layer_selectors(self.num_hidden_layers.value())

    def _update_hidden_sizes(self, count: int):
        # Clear widgets - must remove from layout before deleting
        while self.hidden_sizes_layout.count():
            item = self.hidden_sizes_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._hidden_spinboxes = []

        for i in range(count):
            sb = QSpinBox()
            sb.setRange(1, 1024)
            sb.setValue(4 if i > 0 else 2)
            sb.setPrefix(f"Layer {i+1}: ")
            self.hidden_sizes_layout.addWidget(sb)
            self._hidden_spinboxes.append(sb)

        # Update per-layer activation selectors to match count
        # Clear existing combos and their labels - must remove from layout before deleting
        while self.per_layer_selectors_layout.count():
            item = self.per_layer_selectors_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._per_layer_combos = []
        self._per_layer_combo_rows = []  # Track row widgets for cleanup

        visible = self.per_layer_checkbox.isChecked()
        for i in range(count):
            # Create a row widget with label and combo for each layer
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            label = QLabel(f"Layer {i+1}:")
            combo = QComboBox()
            combo.addItems(["Sigmoid", "ReLU", "Tanh", "Linear"])
            combo.setCurrentText("Sigmoid")
            combo.setEditable(False)
            combo.setToolTip(f"Activation function for hidden layer {i+1}")

            row_layout.addWidget(label)
            row_layout.addWidget(combo)
            row_layout.addStretch()

            row_widget.setVisible(visible)
            self.per_layer_selectors_layout.addWidget(row_widget)
            self._per_layer_combos.append(combo)
            self._per_layer_combo_rows.append(row_widget)

    def _toggle_per_layer_selectors(self, count: int):
        # Ensure per-layer combo widgets exist and show/hide based on checkbox
        visible = self.per_layer_checkbox.isChecked()
        # Toggle label and container visibility
        try:
            self.per_layer_label.setVisible(visible)
            self.per_layer_selectors_widget.setVisible(visible)
        except Exception:
            pass
        # Toggle the row widgets (which contain label + combo)
        for row_widget in getattr(self, "_per_layer_combo_rows", []):
            row_widget.setVisible(visible)

    def _on_generate(self):
        # Read parameters
        num_inputs = int(self.num_inputs.value())
        hidden_layers = [int(sb.value()) for sb in self._hidden_spinboxes]
        num_outputs = int(self.num_outputs.value())

        # Activation selection: per-layer or global
        if self.per_layer_checkbox.isChecked():
            activations = [str(cb.currentText()) for cb in self._per_layer_combos]
        else:
            activations = str(self.global_activation.currentText())

        bias = bool(self.bias_checkbox.isChecked())
        output_activation = str(self.output_activation.currentText())

        try:
            g = self._vm.generate(
                num_inputs,
                hidden_layers,
                num_outputs,
                activations=activations,
                bias=bias,
                output_activation=output_activation,
            )
            # Keep generated graph object
            self._generated_graph = g
            self.accept()
        except Exception as e:
            # Log exception for debugging and reject dialog
            import logging

            logger = logging.getLogger(__name__)
            logger.exception("Failed to generate MLP graph: %s", e)
            self._generated_graph = None
            self.reject()

    def get_graph(self):
        return self._generated_graph

    def closeEvent(self, event):
        try:
            self._vm.cleanup()
        except Exception:
            pass
        event.accept()
