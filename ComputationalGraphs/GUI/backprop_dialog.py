"""Dialog for adding backpropagation to existing MLP."""

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

from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.MLPGraph import MLPGraph


class BackpropDialog(QDialog):
    """Dialog for adding backpropagation to an MLP."""

    def __init__(self, current_graph: Graph, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Backpropagation")
        self.setMinimumWidth(350)

        self.current_graph = current_graph
        self.generated_graph = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Check if current graph is an MLP
        is_mlp = isinstance(self.current_graph, MLPGraph)

        if not is_mlp:
            # Use plain text (no emoji) for cross-platform consistency
            warning = QLabel(
                "Warning: Current graph may not be an MLP.\n"
                "Backpropagation is designed for MLPGraph instances."
            )
            warning.setWordWrap(True)
            warning.setStyleSheet("color: orange; padding: 10px;")
            layout.addWidget(warning)

        # Learning rate
        form_layout = QFormLayout()

        self.learning_rate = QDoubleSpinBox()
        self.learning_rate.setRange(0.0001, 10.0)
        self.learning_rate.setValue(0.01)
        self.learning_rate.setDecimals(4)
        self.learning_rate.setSingleStep(0.01)
        form_layout.addRow("Learning Rate:", self.learning_rate)

        layout.addLayout(form_layout)

        # Info label
        info = QLabel(
            "This will add backpropagation nodes to the current MLP graph. "
            "The graph should be an MLPGraph generated via 'Generate MLP'."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; font-size: 9pt; padding: 10px;")
        layout.addWidget(info)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Add Backpropagation")
        add_btn.clicked.connect(self._add_backprop)
        button_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove Backpropagation")
        remove_btn.clicked.connect(self._remove_backprop)
        button_layout.addWidget(remove_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _add_backprop(self):
        """Add backpropagation to the current graph."""
        try:
            if not isinstance(self.current_graph, MLPGraph):
                reply = QMessageBox.question(
                    self,
                    "Not an MLP",
                    "The current graph is not an MLPGraph instance. "
                    "Backpropagation may not work correctly. Continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            # Create backprop graph
            backprop_graph = BackpropGraph(
                self.current_graph, learningRate=self.learning_rate.value()
            )
            backprop_graph.BuildBackprop()

            # Combine graphs
            full_graph = Graph()
            for node in self.current_graph.nodes:
                full_graph.AddNode(node)
            for node in backprop_graph.nodes:
                full_graph.AddNode(node)
            full_graph.UpdateAdjacencyMatrix()

            self.generated_graph = full_graph
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Adding Backpropagation",
                f"Failed to add backpropagation:\n{str(e)}",
            )

    def _remove_backprop(self):
        """Remove backpropagation nodes from the current graph after confirmation."""
        reply = QMessageBox.question(
            self,
            "Remove Backpropagation",
            "Remove backpropagation nodes from the current graph?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return

        try:
            # Operate on a copy of the graph or the current graph directly
            BackpropGraph.RemoveBackpropFromGraph(self.current_graph)
            QMessageBox.information(self, "Removed", "Backpropagation nodes removed.")
            # Update generated_graph to reflect removal
            self.generated_graph = self.current_graph
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Removing Backpropagation",
                f"Failed to remove backpropagation:\n{str(e)}",
            )

    def get_graph(self) -> Graph:
        """Get the generated graph with backpropagation."""
        return self.generated_graph
