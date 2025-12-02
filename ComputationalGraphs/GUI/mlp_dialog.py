"""Dialog for generating MLP graphs."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
        self.hidden_activation.addItems(["Sigmoid", "ReLU", "Linear"])
        self.hidden_activation.setCurrentText("Sigmoid")
        activation_layout.addRow("Hidden Layers:", self.hidden_activation)

        self.output_activation = QComboBox()
        self.output_activation.addItems(["Sigmoid", "ReLU", "Linear"])
        self.output_activation.setCurrentText("Sigmoid")
        activation_layout.addRow("Output Layer:", self.output_activation)

        activation_group.setLayout(activation_layout)
        layout.addWidget(activation_group)

        # Buttons
        button_layout = QHBoxLayout()

        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self._generate_mlp)
        button_layout.addWidget(generate_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _update_hidden_layer_sizes(self, num_layers: int):
        """Update the hidden layer size inputs based on number of layers."""
        # Clear existing spinboxes
        for spinbox in self.hidden_layer_spinboxes:
            spinbox.deleteLater()
        self.hidden_layer_spinboxes.clear()

        # Add new spinboxes
        for i in range(num_layers):
            spinbox = QSpinBox()
            spinbox.setRange(1, 1000)
            spinbox.setValue(2 if i == 0 else 4)  # Default sizes
            spinbox.setPrefix(f"Layer {i+1}: ")
            self.hidden_layer_container.addWidget(spinbox)
            self.hidden_layer_spinboxes.append(spinbox)

    def _get_activation_class(self, name: str):
        """Get activation function class by name."""
        mapping = {"Sigmoid": SigmoidNode, "ReLU": ReLUNode, "Linear": LinearNode}
        return mapping.get(name, SigmoidNode)

    def _generate_mlp(self):
        """Generate the MLP graph."""
        try:
            # Get hidden layer sizes
            hidden_sizes = [spinbox.value() for spinbox in self.hidden_layer_spinboxes]

            # Get activation functions
            hidden_act = self._get_activation_class(
                self.hidden_activation.currentText()
            )
            output_act = self._get_activation_class(
                self.output_activation.currentText()
            )

            # Create MLP
            mlp_graph = MLPGraph(
                numInputs=self.num_inputs.value(),
                numOutputs=self.num_outputs.value(),
                numHiddenLayers=self.num_hidden_layers.value(),
                hiddenLayerSizes=hidden_sizes,
                activationFunction=hidden_act,
                outputLayerType=output_act,
            )
            mlp_graph.BuildMLP()
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
