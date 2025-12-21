"""
MLP Generator Dialog (new MVVM view) - minimal dialog that uses
`MLPGeneratorViewModel` to create a simple mock graph for examples/tests.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
        self._update_hidden_sizes(self.num_hidden_layers.value())

    def _update_hidden_sizes(self, count: int):
        # Clear widgets
        for sb in list(self._hidden_spinboxes):
            try:
                sb.deleteLater()
            except Exception:
                pass
        self._hidden_spinboxes = []

        for i in range(count):
            sb = QSpinBox()
            sb.setRange(1, 1024)
            sb.setValue(4 if i > 0 else 2)
            sb.setPrefix(f"Layer {i+1}: ")
            self.hidden_sizes_layout.addWidget(sb)
            self._hidden_spinboxes.append(sb)

    def _on_generate(self):
        # Read parameters
        num_inputs = int(self.num_inputs.value())
        hidden_layers = [int(sb.value()) for sb in self._hidden_spinboxes]
        num_outputs = int(self.num_outputs.value())

        try:
            g = self._vm.generate(num_inputs, hidden_layers, num_outputs)
            self._generated_graph = g
            self.accept()
        except Exception as e:
            # Simple failure handling - reject and set generated graph to None
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
