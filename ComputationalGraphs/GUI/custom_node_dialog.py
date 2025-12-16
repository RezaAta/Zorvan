"""
Dialog for creating custom nodes through the GUI.

Users configure BasicNode properties and write the Operation body in Python.
"""

from typing import Any, Dict, List, Optional

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ComputationalGraphs.GUI.custom_node_manager import CustomNodeDefinition


class CustomNodeDialog(QDialog):
    """Dialog for creating or editing custom nodes.

    Guides user through:
    1. Setting node properties (name, input count, batch size, etc.)
    2. Selecting valid input types
    3. Writing the Operation body
    """

    def __init__(self, parent=None, existing_definition=None):
        """Initialize the dialog.

        Args:
            parent: Parent widget
            existing_definition: If editing, the CustomNodeDefinition to modify
        """
        super().__init__(parent)
        self.existing_definition = existing_definition
        self.setWindowTitle(
            "Edit Custom Node" if existing_definition else "Create Custom Node"
        )
        self.setModal(True)
        self.resize(700, 800)

        self.init_ui()

        # If editing, populate with existing values
        if existing_definition:
            self.load_definition(existing_definition)

    def init_ui(self):
        """Build the dialog UI."""
        main_layout = QVBoxLayout(self)

        # Scrollable area for long dialogs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        # ===== SECTION 1: NODE PROPERTIES =====
        props_group = QGroupBox("Node Properties")
        props_layout = QVBoxLayout()

        # Type name
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type Name:"))
        self.type_name_edit = QLineEdit()
        self.type_name_edit.setPlaceholderText("e.g., MyCustomNode")
        type_layout.addWidget(self.type_name_edit)
        props_layout.addLayout(type_layout)

        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description for palette")
        desc_layout.addWidget(self.description_edit)
        props_layout.addLayout(desc_layout)

        # Input count
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Number of Inputs:"))
        self.input_count_spin = QSpinBox()
        self.input_count_spin.setMinimum(1)
        self.input_count_spin.setMaximum(10)
        self.input_count_spin.setValue(2)
        self.input_count_spin.valueChanged.connect(self.on_input_count_changed)
        input_layout.addWidget(self.input_count_spin)
        input_layout.addStretch()
        props_layout.addLayout(input_layout)

        # Batch size
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(10)
        self.batch_size_spin.setValue(2)
        batch_layout.addWidget(self.batch_size_spin)
        batch_layout.addStretch()
        props_layout.addLayout(batch_layout)

        # Inclusive checkbox
        self.inclusive_check = QCheckBox("Inclusive (add result to next batch)")
        self.inclusive_check.setChecked(True)
        props_layout.addWidget(self.inclusive_check)

        # Forced batch processing checkbox
        self.forced_batch_check = QCheckBox(
            "Forced Batch Processing (continue until insufficient inputs)"
        )
        self.forced_batch_check.setChecked(False)
        props_layout.addWidget(self.forced_batch_check)

        props_group.setLayout(props_layout)
        content_layout.addWidget(props_group)

        # ===== SECTION 2: VALID INPUT TYPES =====
        types_group = QGroupBox("Valid Input Types")
        types_layout = QVBoxLayout()

        self.valid_types_checks = {}
        for type_name in ["numeric", "string", "array", "none"]:
            check = QCheckBox(type_name.capitalize())
            self.valid_types_checks[type_name] = check
            types_layout.addWidget(check)

        # Set numeric as default
        self.valid_types_checks["numeric"].setChecked(True)
        types_group.setLayout(types_layout)
        content_layout.addWidget(types_group)

        # ===== SECTION 3: CUSTOM PROPERTIES =====
        custom_props_group = QGroupBox("Custom Properties (Optional)")
        custom_props_layout = QVBoxLayout()

        # Container widget for property rows
        self.custom_props_widget = QWidget()
        self.custom_props_container = QVBoxLayout(self.custom_props_widget)
        self.custom_props_container.setContentsMargins(0, 0, 0, 0)
        custom_props_layout.addWidget(self.custom_props_widget)

        # List to track property widgets
        self.custom_property_rows: List[Dict[str, QWidget]] = []

        # Add property button (use plain text instead of emoji)
        add_prop_btn = QPushButton("Add Property")
        add_prop_btn.clicked.connect(lambda: self.add_custom_property_row())
        custom_props_layout.addWidget(add_prop_btn)

        custom_props_group.setLayout(custom_props_layout)
        content_layout.addWidget(custom_props_group)

        # ===== SECTION 4: OPERATION CODE =====
        op_group = QGroupBox("Operation Body")
        op_layout = QVBoxLayout()

        # Placeholder label
        self.placeholder_label = QLabel("Use variables: input1, input2")
        self.placeholder_label.setStyleSheet("color: #888; font-style: italic;")
        op_layout.addWidget(self.placeholder_label)

        # Code editor
        self.operation_edit = QPlainTextEdit()
        self.operation_edit.setFont(QFont("Courier", 10))
        self.operation_edit.setPlaceholderText(
            "# Write the operation body here\n"
            "# Use input1, input2, ... for inputs\n"
            "# Return a single value\n\n"
            "return input1 + input2"
        )
        self.operation_edit.setMinimumHeight(250)
        op_layout.addWidget(self.operation_edit)

        op_group.setLayout(op_layout)
        content_layout.addWidget(op_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # ===== BUTTONS =====
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept_and_validate)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def on_input_count_changed(self, value: int):
        """Update placeholder when input count changes."""
        inputs = ", ".join(f"input{i+1}" for i in range(value))
        self.placeholder_label.setText(f"Use variables: {inputs}")

    def add_custom_property_row(
        self, name: str = "", prop_type: str = "any", default_value: str = "None"
    ):
        """Add a new custom property row to the UI.

        Args:
            name: Property name
            prop_type: Property type ("any", "int", "float", "str", "bool", "node")
            default_value: Default value as string
        """
        row_layout = QHBoxLayout()

        # Property name
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Property name")
        name_edit.setText(name)
        name_edit.setMinimumWidth(120)
        row_layout.addWidget(name_edit)

        # Property type
        type_combo = QComboBox()
        type_combo.addItems(["any", "int", "float", "str", "bool", "node"])
        type_combo.setCurrentText(prop_type)
        type_combo.setMinimumWidth(80)
        row_layout.addWidget(type_combo)

        # Default value
        default_edit = QLineEdit()
        default_edit.setPlaceholderText("Default value (Python)")
        default_edit.setText(default_value)
        default_edit.setMinimumWidth(150)
        row_layout.addWidget(default_edit)

        # Remove button (plain text)
        remove_btn = QPushButton("Remove")
        remove_btn.setMaximumWidth(30)
        row_layout.addWidget(remove_btn)

        # Container widget for the row
        row_widget = QWidget()
        row_widget.setLayout(row_layout)

        # Store references
        row_data = {
            "widget": row_widget,
            "name_edit": name_edit,
            "type_combo": type_combo,
            "default_edit": default_edit,
        }
        self.custom_property_rows.append(row_data)

        # Connect remove button
        remove_btn.clicked.connect(lambda: self.remove_custom_property_row(row_data))

        # Add to container
        self.custom_props_container.addWidget(row_widget)

    def remove_custom_property_row(self, row_data: Dict[str, QWidget]):
        """Remove a custom property row from the UI."""
        if row_data in self.custom_property_rows:
            self.custom_property_rows.remove(row_data)
            row_data["widget"].deleteLater()

    def get_custom_properties(self) -> List[Dict[str, Any]]:
        """Get all custom properties from the UI.

        Returns:
            List of property dictionaries with name, type, default_value
        """
        properties = []
        for row in self.custom_property_rows:
            name = row["name_edit"].text().strip()
            if name:  # Only include properties with a name
                properties.append(
                    {
                        "name": name,
                        "type": row["type_combo"].currentText(),
                        "default_value": row["default_edit"].text().strip() or "None",
                    }
                )
        return properties

    def load_definition(self, definition: CustomNodeDefinition):
        """Load an existing definition for editing."""
        self.type_name_edit.setText(definition.type_name)
        self.description_edit.setText(definition.description)
        self.input_count_spin.setValue(definition.input_count)
        self.batch_size_spin.setValue(definition.batch_size)
        self.inclusive_check.setChecked(definition.inclusive)
        self.forced_batch_check.setChecked(definition.forced_batch_processing)

        # Set valid input types
        for type_name, check in self.valid_types_checks.items():
            check.setChecked(type_name in definition.valid_input_types)

        # Set operation code
        self.operation_edit.setPlainText(definition.operation_code)

        # Load custom properties
        for prop in definition.custom_properties:
            self.add_custom_property_row(
                name=prop.get("name", ""),
                prop_type=prop.get("type", "any"),
                default_value=prop.get("default_value", "None"),
            )

    def get_definition(self) -> CustomNodeDefinition:
        """Build and return a CustomNodeDefinition from the dialog values."""
        valid_types = [
            t for t, check in self.valid_types_checks.items() if check.isChecked()
        ]

        return CustomNodeDefinition(
            type_name=self.type_name_edit.text().strip(),
            input_count=self.input_count_spin.value(),
            batch_size=self.batch_size_spin.value(),
            inclusive=self.inclusive_check.isChecked(),
            forced_batch_processing=self.forced_batch_check.isChecked(),
            valid_input_types=valid_types or ["numeric"],  # Default to numeric
            operation_code=self.operation_edit.toPlainText().strip(),
            description=self.description_edit.text().strip(),
            custom_properties=self.get_custom_properties(),
        )

    def accept_and_validate(self):
        """Validate and save the definition."""
        # Get the definition
        definition = self.get_definition()

        # Validate type name
        if not definition.type_name:
            QMessageBox.warning(self, "Invalid Input", "Type Name cannot be empty.")
            return

        if not definition.type_name.replace("_", "").isalnum():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Type Name must contain only alphanumeric characters and underscores.",
            )
            return

        # Validate operation code
        error = definition.validate_operation_code()
        if error:
            QMessageBox.warning(
                self,
                "Invalid Operation Code",
                f"Error in operation code:\n\n{error}",
            )
            return

        # Validate operation code uses correct input variables
        expected_inputs = {f"input{i+1}" for i in range(definition.input_count)}
        # Simple check: look for inputX patterns in the code
        import re

        used_inputs = set(re.findall(r"input\d+", definition.operation_code))

        # Warn if inputs are not used (but don't block)
        if definition.input_count > 0 and not used_inputs:
            reply = QMessageBox.warning(
                self,
                "Unused Inputs",
                f"Operation code does not use any input variables.\n"
                f"Expected: {', '.join(sorted(expected_inputs))}\n\n"
                f"Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # All good
        # Prevent conflicts with built-in or other custom nodes
        # Check for name conflicts with built-in or other custom nodes
        err = self._check_name_conflict(definition.type_name)
        if err:
            QMessageBox.warning(self, "Name Conflict", err)
            return

        self.definition = definition
        self.accept()

    def _check_name_conflict(self, new_name: str) -> Optional[str]:
        """Return an error message if new_name conflicts with existing types,
        else None.
        """
        try:
            from ComputationalGraphs.GUI.custom_node_manager import (
                get_custom_node_manager,
            )
            from ComputationalGraphs.GUI.node_factory import is_builtin_node

            manager = get_custom_node_manager()
            # Create flow: no existing_definition -> creating new node
            if self.existing_definition is None:
                # Check built-ins
                if is_builtin_node(new_name):
                    return (
                        "Name '"
                        + new_name
                        + "' conflicts with an existing built-in node type."
                    )
                # Check other custom definitions
                if manager.get_definition(new_name) is not None:
                    return (
                        "Name '"
                        + new_name
                        + "' is already used by another custom node."
                    )
            else:
                # Editing existing definition - if the name changed, check collisions
                if new_name != self.existing_definition.type_name:
                    # Built-in conflict
                    if is_builtin_node(new_name):
                        return (
                            "Name '"
                            + new_name
                            + "' conflicts with an existing built-in node type."
                        )
                    existing_def = manager.get_definition(new_name)
                    if existing_def is not None and (
                        existing_def.type_name != self.existing_definition.type_name
                    ):
                        return (
                            "Name '"
                            + new_name
                            + "' is already used by another custom node."
                        )
        except Exception:
            # If manager or factory isn't available, be permissive
            return None
        return None
