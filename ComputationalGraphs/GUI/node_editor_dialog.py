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


class NodeEditorDialog(QDialog):
    """Dialog for editing node properties and initial values."""

    def __init__(self, node, parent=None):
        super().__init__(parent)

        self.node = node
        self.setWindowTitle(f"Edit Node: {node.name}")
        self.setModal(True)
        self.resize(500, 400)

        # Storage for parameter widgets
        self.param_widgets = {}

        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Basic properties section
        basic_group = QGroupBox("Basic Properties")
        basic_layout = QFormLayout()

        # Node name
        self.name_edit = QLineEdit(self.node.name)
        basic_layout.addRow("Name:", self.name_edit)

        # Node type (read-only)
        type_label = QLabel(type(self.node).__name__)
        basic_layout.addRow("Type:", type_label)

        # Current value (editable)
        self.value_edit = QTextEdit()
        self.value_edit.setMaximumHeight(60)
        # For BufferNode, show both the 'current' (oldest/delayed) value and the most recent appended value
        if hasattr(self.node, "buffer"):
            curVal = self.node.value
            curStr = str(curVal) if curVal is not None else "None"
            value_str = curStr
        else:
            value_str = str(self.node.value) if self.node.value is not None else "None"
        self.value_edit.setPlainText(value_str)
        self.value_edit.setToolTip(
            "Edit the current value of this node (use Python syntax)"
        )
        basic_layout.addRow("Current Value:", self.value_edit)

        # Forced batch processing checkbox
        self.forced_batch_checkbox = QCheckBox()
        self.forced_batch_checkbox.setChecked(
            getattr(self.node, "forcedBatchProcessing", False)
        )
        self.forced_batch_checkbox.setToolTip(
            "When enabled, ProcessBatch will continue processing until all inputs "
            "are consumed. Useful for nodes that need to aggregate multiple inputs."
        )
        basic_layout.addRow("Forced Batch Processing:", self.forced_batch_checkbox)

        # Incremental checkbox for ContainerNode and InitializableContainerNode
        if hasattr(self.node, "Incremental"):
            self.incremental_checkbox = QCheckBox()
            self.incremental_checkbox.setChecked(
                getattr(self.node, "Incremental", False)
            )
            self.incremental_checkbox.setToolTip(
                "When enabled, the node adds predecessor values to its current value. "
                "When disabled, it subtracts them. Used for weight updates in training."
            )
            basic_layout.addRow("Incremental:", self.incremental_checkbox)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Parameters section (dynamically generated)
        self.add_parameter_editors(layout)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def add_parameter_editors(self, layout):
        """Dynamically add editors for all __init__ parameters of the node."""
        # Get the __init__ signature
        sig = inspect.signature(self.node.__class__.__init__)

        # Skip 'self', 'name', and 'value' as they're handled separately
        skip_params = {"self", "name", "value"}

        param_group = QGroupBox("Parameters")
        param_layout = QFormLayout()

        has_params = False
        for param_name, param in sig.parameters.items():
            if param_name in skip_params:
                continue

            has_params = True

            # Get current value from node
            # Special case: BufferNode stores 'data' in 'buffer'
            if (
                param_name == "data"
                and hasattr(self.node, "buffer")
                and not hasattr(self.node, "data")
            ):
                current_value = self.node.buffer
            # Special case: BufferNode-based nodes store 'size' in 'bufferSize'
            elif param_name == "size" and hasattr(self.node, "bufferSize"):
                current_value = self.node.bufferSize
            else:
                current_value = getattr(self.node, param_name, param.default)

            # Determine widget type based on current value and annotation
            widget = self.create_widget_for_parameter(param_name, current_value, param)

            if widget:
                self.param_widgets[param_name] = widget
                # Create a nice label (convert snake_case to Title Case)
                label = param_name.replace("_", " ").title() + ":"
                param_layout.addRow(label, widget)

        if has_params:
            param_group.setLayout(param_layout)
            layout.addWidget(param_group)

        # Special section for CompressedNode to show internal nodes
        if type(self.node).__name__ == "CompressedNode":
            self.add_compressed_node_info(layout)

        # Special section for AbstractNode to show internal nodes
        if type(self.node).__name__ == "AbstractNode":
            self.add_abstract_node_info(layout)

        # Special actions for PopulationNode
        if type(self.node).__name__ == "PopulationNode":
            self.add_population_actions(layout)

        # Special actions for nodes that have a reinitialize method
        if hasattr(self.node, "reinitialize"):
            self.add_initializable_actions(layout)

    def add_population_actions(self, layout):
        """Add special action buttons for PopulationNode."""
        actions_group = QGroupBox("Population Actions")
        actions_layout = QVBoxLayout()

        # Regenerate button
        regen_btn = QPushButton("Regenerate Population")
        regen_btn.setToolTip("Generate a new random population with current parameters")
        regen_btn.clicked.connect(self.on_regenerate_population)
        actions_layout.addWidget(regen_btn)

        # Stats display
        stats_btn = QPushButton("Show Statistics")
        stats_btn.setToolTip("Display current population statistics")
        stats_btn.clicked.connect(self.on_show_population_stats)
        actions_layout.addWidget(stats_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

    def add_initializable_actions(self, layout):
        """Add reinitialize button for nodes that support reinitialization."""
        actions_group = QGroupBox("Initialization Actions")
        actions_layout = QVBoxLayout()

        reinit_btn = QPushButton("🎲 Reinitialize")
        reinit_btn.setToolTip("Randomize this node's value using configured init range")
        reinit_btn.clicked.connect(self.on_reinitialize_weight)
        actions_layout.addWidget(reinit_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

    def add_compressed_node_info(self, layout):
        """Add a readonly section showing internal nodes of a CompressedNode."""
        from PyQt6.QtWidgets import QAbstractItemView, QListWidget

        info_group = QGroupBox("Internal Nodes (Chain)")
        info_layout = QVBoxLayout()

        # Create a readonly list widget
        list_widget = QListWidget()
        list_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        # Populate with internal nodes
        internal_nodes = getattr(self.node, "listOfNodes", [])
        for i, node in enumerate(internal_nodes):
            node_name = getattr(node, "name", str(node))
            node_type = type(node).__name__
            node_value = getattr(node, "value", "N/A")
            # Format value for display
            if isinstance(node_value, float):
                value_str = f"{node_value:.4f}"
            else:
                value_str = str(node_value)[:20]
            list_widget.addItem(f"{i+1}. {node_name} ({node_type}) = {value_str}")

        list_widget.setMaximumHeight(150)
        info_layout.addWidget(list_widget)

        # Show count
        count_label = QLabel(f"Total: {len(internal_nodes)} nodes in chain")
        info_layout.addWidget(count_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

    def add_abstract_node_info(self, layout):
        """Add a readonly section showing internal nodes of an AbstractNode."""
        from PyQt6.QtWidgets import QAbstractItemView, QListWidget

        info_group = QGroupBox("Internal Nodes (Disjoint Set)")
        info_layout = QVBoxLayout()

        # Create a readonly list widget
        list_widget = QListWidget()
        list_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        # Populate with internal nodes
        internal_nodes = getattr(self.node, "listOfNodes", [])
        for i, node in enumerate(internal_nodes):
            node_name = getattr(node, "name", str(node))
            node_type = type(node).__name__
            node_value = getattr(node, "value", "N/A")
            # Format value for display
            if isinstance(node_value, float):
                value_str = f"{node_value:.4f}"
            elif isinstance(node_value, list):
                # For lists (like nested abstract nodes), show summary
                if len(node_value) <= 3:
                    value_str = str(node_value)
                else:
                    value_str = f"[{len(node_value)} items]"
            else:
                value_str = str(node_value)[:20]
            list_widget.addItem(f"- {node_name} ({node_type}) = {value_str}")

        # Set height based on number of nodes, but cap at reasonable size
        row_height = 20
        max_rows = 8
        visible_rows = min(len(internal_nodes), max_rows)
        list_widget.setMaximumHeight(max(visible_rows * row_height + 10, 60))
        info_layout.addWidget(list_widget)

        # Show count and hint about parallel execution
        count_label = QLabel(
            f"Total: {len(internal_nodes)} nodes (processed in parallel)"
        )
        info_layout.addWidget(count_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

    def on_regenerate_population(self):
        """Regenerate the population with current parameters."""
        if hasattr(self.node, "regenerate_population"):
            # First update ALL parameters from widgets (including size!)
            for param_name, widget in self.param_widgets.items():
                new_value = None

                if isinstance(widget, QCheckBox):
                    new_value = widget.isChecked()
                elif isinstance(widget, QComboBox):
                    new_value = widget.currentText()
                elif isinstance(widget, QSpinBox):
                    new_value = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    new_value = widget.value()
                elif isinstance(widget, QLineEdit):
                    new_value = widget.text()
                elif isinstance(widget, QTextEdit):
                    text = widget.toPlainText().strip()
                    try:
                        if text.lower() == "none":
                            new_value = None
                        else:
                            new_value = ast.literal_eval(text)
                    except (ValueError, SyntaxError):
                        new_value = text

                # Update the node attribute
                if param_name == "size":
                    # For PopulationNode, size should update bufferSize
                    self.node.bufferSize = new_value
                    setattr(self.node, param_name, new_value)
                elif (
                    param_name == "data"
                    and hasattr(self.node, "buffer")
                    and not hasattr(self.node, "data")
                ):
                    # Skip data for now, will be regenerated
                    pass
                else:
                    setattr(self.node, param_name, new_value)

            # Now regenerate with updated parameters
            new_pop = self.node.regenerate_population()

            # Update the data display
            if "data" in self.param_widgets:
                widget = self.param_widgets["data"]
                if isinstance(widget, QTextEdit):
                    widget.setPlainText(str(new_pop))

            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(
                self,
                "Population Regenerated",
                f"Generated new population:\n"
                f"Size: {len(new_pop)}\n"
                f"Genome Length: {len(new_pop[0]) if new_pop else 0}",
            )

    def on_show_population_stats(self):
        """Show statistics about the current population."""
        if hasattr(self.node, "get_population_stats"):
            stats = self.node.get_population_stats()

            from PyQt6.QtWidgets import QMessageBox

            stats_text = "\n".join(
                [
                    f"{key.replace('_', ' ').title()}: {value}"
                    for key, value in stats.items()
                ]
            )
            QMessageBox.information(self, "Population Statistics", stats_text)

    def on_reinitialize_weight(self):
        """Handle the reinitialize action for nodes with a reinitialize() method."""
        if not hasattr(self.node, "reinitialize"):
            return

        # Update parameters on the node (so init_low/init_high changes are applied)
        try:
            self.update_node_parameters_from_widgets()
        except Exception:
            pass

        try:
            new_val = self.node.reinitialize()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Reinitialize Failed", f"Error: {e}")
            return

        # Update displayed value
        try:
            self.value_edit.setPlainText(
                str(new_val) if new_val is not None else "None"
            )
        except Exception:
            pass

        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            self, "Reinitialized", f"Node {self.node.name} value set to: {new_val}"
        )

    def update_node_parameters_from_widgets(self):
        """Update node parameters from widget values without closing dialog."""
        for param_name, widget in self.param_widgets.items():
            new_value = None

            if isinstance(widget, QCheckBox):
                new_value = widget.isChecked()
            elif isinstance(widget, QComboBox):
                new_value = widget.currentText()
            elif isinstance(widget, QSpinBox):
                new_value = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                new_value = widget.value()
            elif isinstance(widget, QLineEdit):
                new_value = widget.text()
            elif isinstance(widget, QTextEdit):
                text = widget.toPlainText().strip()
                try:
                    if text.lower() == "none":
                        new_value = None
                    else:
                        new_value = ast.literal_eval(text)
                except (ValueError, SyntaxError):
                    new_value = text

            # Set the attribute
            if (
                param_name == "data"
                and hasattr(self.node, "buffer")
                and not hasattr(self.node, "data")
            ):
                if new_value is not None:
                    self.node.buffer = (
                        list(new_value)
                        if isinstance(new_value, (list, tuple))
                        else [new_value]
                    )
                    self.node.bufferSize = max(
                        self.node.bufferSize, len(self.node.buffer)
                    )
                    self.node.value = self.node.buffer[0] if self.node.buffer else None
            else:
                setattr(self.node, param_name, new_value)

    def create_widget_for_parameter(self, param_name, current_value, param):
        """Create an appropriate widget for a parameter based on its type."""
        # Handle None/missing values - use default
        if current_value is inspect.Parameter.empty:
            current_value = None

        # Special handling for MovingAverageNode 'mode' parameter
        if param_name == "mode" and type(self.node).__name__ == "MovingAverageNode":
            widget = QComboBox()
            widget.addItems(["continuous", "batch"])
            current_mode = (
                str(current_value) if current_value is not None else "continuous"
            )
            index = widget.findText(current_mode)
            if index >= 0:
                widget.setCurrentIndex(index)
            return widget

        # Special handling for 'init_method' parameter on InitializableContainerNode
        if param_name == "init_method" and hasattr(self.node, "init_method"):
            widget = QComboBox()
            widget.addItems(["uniform", "normal"])
            current_mode = (
                str(current_value) if current_value is not None else "uniform"
            )
            index = widget.findText(current_mode)
            if index >= 0:
                widget.setCurrentIndex(index)
            return widget

        # Determine type from annotation or current value
        param_type = None
        if param.annotation != inspect.Parameter.empty:
            param_type = param.annotation
        elif current_value is not None:
            param_type = type(current_value)

        # Create appropriate widget
        if param_type == bool or isinstance(current_value, bool):
            widget = QCheckBox()
            widget.setChecked(
                bool(current_value) if current_value is not None else False
            )
            return widget

        elif param_type == int or isinstance(current_value, int):
            widget = QSpinBox()
            widget.setRange(-1000000, 1000000)
            widget.setValue(int(current_value) if current_value is not None else 0)
            return widget

        elif param_type == float or isinstance(current_value, float):
            widget = QDoubleSpinBox()
            widget.setRange(-1000000.0, 1000000.0)
            widget.setDecimals(6)
            widget.setValue(float(current_value) if current_value is not None else 0.0)
            return widget

        elif param_type == str or isinstance(current_value, str):
            widget = QLineEdit()
            widget.setText(str(current_value) if current_value is not None else "")
            return widget

        elif isinstance(current_value, (list, tuple)):
            # For lists/arrays, use a text edit
            widget = QTextEdit()
            widget.setMaximumHeight(80)
            widget.setPlainText(str(current_value))
            widget.setToolTip(
                "Enter Python list/tuple syntax, e.g., [1, 2, 3] or (4, 5)"
            )
            return widget

        else:
            # Generic text edit for complex types
            widget = QTextEdit()
            widget.setMaximumHeight(80)
            widget.setPlainText(
                str(current_value) if current_value is not None else "None"
            )
            widget.setToolTip(f"Enter value for {param_name} (Python syntax)")
            return widget

    def save_changes(self):
        """Save the edited properties back to the node."""
        try:
            # Update name
            self.node.name = self.name_edit.text()

            # Update current value
            try:
                value_str = self.value_edit.toPlainText().strip()
                if value_str.lower() == "none":
                    self.node.value = None
                else:
                    # Try to parse as Python literal
                    self.node.value = ast.literal_eval(value_str)
            except (ValueError, SyntaxError):
                # If parsing fails, treat as string
                self.node.value = self.value_edit.toPlainText()

            # Update forced batch processing
            self.node.forcedBatchProcessing = self.forced_batch_checkbox.isChecked()

            # Update Incremental property for ContainerNode types
            if hasattr(self, "incremental_checkbox") and hasattr(
                self.node, "Incremental"
            ):
                self.node.Incremental = self.incremental_checkbox.isChecked()

            # Update all dynamic parameters
            for param_name, widget in self.param_widgets.items():
                new_value = None

                if isinstance(widget, QCheckBox):
                    new_value = widget.isChecked()

                elif isinstance(widget, QSpinBox):
                    new_value = widget.value()

                elif isinstance(widget, QDoubleSpinBox):
                    new_value = widget.value()

                elif isinstance(widget, QLineEdit):
                    new_value = widget.text()

                elif isinstance(widget, QTextEdit):
                    # Try to parse as Python literal for lists/complex types
                    text = widget.toPlainText().strip()
                    try:
                        if text.lower() == "none":
                            new_value = None
                        else:
                            new_value = ast.literal_eval(text)
                    except (ValueError, SyntaxError):
                        # If parsing fails, store as string
                        new_value = text

                # Special case: BufferNode's 'data' parameter is stored in 'buffer'
                if (
                    param_name == "data"
                    and hasattr(self.node, "buffer")
                    and not hasattr(self.node, "data")
                ):
                    if new_value is not None:
                        self.node.buffer = (
                            list(new_value)
                            if isinstance(new_value, (list, tuple))
                            else [new_value]
                        )
                        self.node.bufferSize = max(
                            self.node.bufferSize, len(self.node.buffer)
                        )
                        self.node.value = (
                            self.node.buffer[0] if self.node.buffer else None
                        )
                elif param_name == "size" and hasattr(self.node, "bufferSize"):
                    # For BufferNode-based nodes (including MovingAverageNode), update bufferSize and reconstruct buffer
                    old_buffer = (
                        self.node.buffer[:] if hasattr(self.node, "buffer") else []
                    )
                    self.node.bufferSize = new_value
                    setattr(self.node, param_name, new_value)
                    # Reconstruct buffer with new size, preserving existing values
                    if hasattr(self.node, "buffer"):
                        self.node.buffer = (
                            old_buffer[-new_value:]
                            if len(old_buffer) > new_value
                            else old_buffer
                        )
                else:
                    setattr(self.node, param_name, new_value)

            # Handle special cases for specific node types
            if hasattr(self.node, "currentIndex") and "data" in self.param_widgets:
                # DataStreamNode: reset index when data changes
                self.node.currentIndex = 0

            self.accept()

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Error", f"Failed to save changes: {str(e)}")
