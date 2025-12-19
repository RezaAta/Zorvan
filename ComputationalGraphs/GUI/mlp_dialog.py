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


class MLPGeneratorDialog(QDialog):
    """Dialog for configuring and generating MLP graphs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate MLP")
        self.setMinimumWidth(400)
        self.generated_graph = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Architecture group
        arch_group = QGroupBox("Network Architecture")
        arch_layout = QFormLayout()

        self.num_inputs = QSpinBox()
        self.num_inputs.setRange(1, 1000)
        self.num_inputs.setValue(2)
        arch_layout.addRow("Number of Inputs:", self.num_inputs)

        self.num_outputs = QSpinBox()
        self.num_outputs.setRange(1, 1000)
        self.num_outputs.setValue(1)
        arch_layout.addRow("Number of Outputs:", self.num_outputs)

        self.num_hidden_layers = QSpinBox()
        self.num_hidden_layers.setRange(0, 10)
        self.num_hidden_layers.setValue(1)
        self.num_hidden_layers.valueChanged.connect(self._update_hidden_layer_sizes)
        arch_layout.addRow("Number of Hidden Layers:", self.num_hidden_layers)

        # Container for hidden layer size inputs
        self.hidden_layer_widget = QWidget()
        self.hidden_layer_container = QVBoxLayout(self.hidden_layer_widget)
        self.hidden_layer_container.setContentsMargins(0, 0, 0, 0)
        arch_layout.addRow("Hidden Layer Sizes:", self.hidden_layer_widget)

        self.hidden_layer_spinboxes = []
        self._update_hidden_layer_sizes(1)  # Initialize with 1 layer

        arch_group.setLayout(arch_layout)
        layout.addWidget(arch_group)

        # Activation functions group
        activation_group = QGroupBox("Activation Functions")
        activation_layout = QFormLayout()

        self.hidden_activation = QComboBox()
        self.hidden_activation.addItems(["Sigmoid", "ReLU", "Linear", "Tanh"])
        self.hidden_activation.setCurrentText("Sigmoid")
        activation_layout.addRow("Hidden Layers:", self.hidden_activation)

        # Per-layer activation option
        self.per_layer_checkbox = QCheckBox("Per-layer activations")
        self.per_layer_checkbox.stateChanged.connect(self._toggle_per_layer_selectors)
        activation_layout.addRow(self.per_layer_checkbox)

        # Container for per-layer selectors (hidden/added only when enabled)
        self.per_layer_selectors_widget = QWidget()
        self.per_layer_selectors_layout = QVBoxLayout(self.per_layer_selectors_widget)
        self.per_layer_selectors_layout.setContentsMargins(0, 0, 0, 0)
        self.per_layer_selectors = []
        activation_layout.addRow(self.per_layer_selectors_widget)

        self.output_activation = QComboBox()
        self.output_activation.addItems(["Sigmoid", "ReLU", "Linear", "Tanh"])
        self.output_activation.setCurrentText("Sigmoid")
        activation_layout.addRow("Output Layer:", self.output_activation)

        activation_group.setLayout(activation_layout)
        layout.addWidget(activation_group)

        # Buttons
        button_layout = QHBoxLayout()

        generate_btn = QPushButton("Generate")
        try:
            generate_btn.setProperty("themed", True)
            generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            generate_btn.setMouseTracking(True)
        except Exception:
            pass
        generate_btn.clicked.connect(self._generate_mlp)
        button_layout.addWidget(generate_btn)

        cancel_btn = QPushButton("Cancel")
        try:
            cancel_btn.setProperty("themed", True)
            cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cancel_btn.setMouseTracking(True)
        except Exception:
            pass
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Additional options: Create MSE nodes for plotting
        options_group = QGroupBox("Options")
        options_layout = QFormLayout()
        self.create_mse_checkbox = QCheckBox("Create MSE nodes for plotting")
        self.create_mse_checkbox.setChecked(True)  # Default to enabled for plotting
        self.mse_buffer_size = QSpinBox()
        self.mse_buffer_size.setRange(1, 1000000)
        self.mse_buffer_size.setValue(6)
        options_layout.addRow(self.create_mse_checkbox)
        options_layout.addRow("MSE buffer size:", self.mse_buffer_size)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

    def _update_hidden_layer_sizes(self, num_layers: int):
        """Update the hidden layer size inputs based on number of layers."""
        # Clear existing spinboxes
        for spinbox in self.hidden_layer_spinboxes:
            spinbox.deleteLater()
        self.hidden_layer_spinboxes.clear()

        # Clear per-layer selectors if present
        for cb in getattr(self, "per_layer_selectors", []):
            try:
                cb.deleteLater()
            except Exception:
                pass
        self.per_layer_selectors = []

        # Add new spinboxes and (optionally) selectors
        for i in range(num_layers):
            spinbox = QSpinBox()
            spinbox.setRange(1, 1000)
            spinbox.setValue(2 if i == 0 else 4)  # Default sizes
            spinbox.setPrefix(f"Layer {i+1}: ")
            self.hidden_layer_container.addWidget(spinbox)
            self.hidden_layer_spinboxes.append(spinbox)

            # If per-layer mode is active, add a selector
            if (
                getattr(self, "per_layer_checkbox", None)
                and self.per_layer_checkbox.isChecked()
            ):
                selector = QComboBox()
                selector.addItems(["Sigmoid", "ReLU", "Linear", "Tanh"])
                selector.setCurrentText("Sigmoid")
                self.per_layer_selectors_layout.addWidget(selector)
                self.per_layer_selectors.append(selector)

        # Hide or show the selectors widget based on checkbox
        if getattr(self, "per_layer_selectors_widget", None) is not None:
            self.per_layer_selectors_widget.setVisible(
                getattr(self, "per_layer_checkbox", None)
                and self.per_layer_checkbox.isChecked()
            )

    def _toggle_per_layer_selectors(self, state):
        """Toggle per-layer activation selectors visibility based on checkbox."""
        checked = state == 2 or state == Qt.Checked
        # If enabling, create selectors to match current hidden layer count without
        # rebuilding the hidden layer spinboxes (so user-entered sizes are preserved)
        if checked:
            # Clear any existing selectors first
            for cb in list(self.per_layer_selectors):
                try:
                    cb.deleteLater()
                except Exception:
                    pass
            self.per_layer_selectors = []

            # Create selectors for each existing hidden layer spinbox
            for _ in self.hidden_layer_spinboxes:
                selector = QComboBox()
                selector.addItems(["Sigmoid", "ReLU", "Linear", "Tanh"])
                selector.setCurrentText("Sigmoid")
                self.per_layer_selectors_layout.addWidget(selector)
                self.per_layer_selectors.append(selector)

            self.per_layer_selectors_widget.setVisible(True)
        else:
            # Remove selectors
            for cb in list(self.per_layer_selectors):
                try:
                    cb.deleteLater()
                except Exception:
                    pass
            self.per_layer_selectors = []
            self.per_layer_selectors_widget.setVisible(False)

    def _get_activation_class(self, name: str):
        """Get activation function class by name."""
        mapping = {
            "Sigmoid": SigmoidNode,
            "ReLU": ReLUNode,
            "Linear": LinearNode,
            "Tanh": TanhNode,
        }
        return mapping.get(name, SigmoidNode)

    def _generate_mlp(self):
        """Generate the MLP graph."""
        try:
            # Get hidden layer sizes
            hidden_sizes = [spinbox.value() for spinbox in self.hidden_layer_spinboxes]

            # Get activation functions
            output_act = self._get_activation_class(
                self.output_activation.currentText()
            )

            if (
                getattr(self, "per_layer_checkbox", None)
                and self.per_layer_checkbox.isChecked()
            ):
                # Per-layer activations selected
                hidden_acts = [
                    self._get_activation_class(cb.currentText())
                    for cb in self.per_layer_selectors
                ]
                activation_arg = None
                hidden_activation_arg = hidden_acts
            else:
                hidden_act = self._get_activation_class(
                    self.hidden_activation.currentText()
                )
                activation_arg = hidden_act
                hidden_activation_arg = None

            # Create MLP
            mlp_graph = MLPGraph(
                numInputs=self.num_inputs.value(),
                numOutputs=self.num_outputs.value(),
                numHiddenLayers=self.num_hidden_layers.value(),
                hiddenLayerSizes=hidden_sizes,
                activationFunction=activation_arg,
                hiddenActivationFunctions=hidden_activation_arg,
                outputLayerType=output_act,
            )
            mlp_graph.BuildMLP()
            # Optionally create error/MSE buffers for plotting in the GUI, if requested
            try:
                if self.create_mse_checkbox.isChecked():
                    mlp_graph.CreateErrorBuffers(
                        bufferSize=self.mse_buffer_size.value()
                    )
            except Exception:
                # Swallow errors here (CreateErrorBuffers may depend on loaded data shape)
                pass
            mlp_graph.UpdateAdjacencyMatrix()

            self.generated_graph = mlp_graph
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Error Generating MLP", f"Failed to generate MLP:\n{str(e)}"
            )

    def get_graph(self) -> Graph:
        """Get the generated graph."""
        return self.generated_graph
