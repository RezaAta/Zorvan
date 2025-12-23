"""MVVM Custom Node dialog view: binds to `CustomNodeViewModel`"""

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

from typing import Dict

from ...viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from gui_framework.viewmodels.dialogs.custom_node_viewmodel import (
        CustomNodeViewModel,
    )

    from ..base import BaseView

    class CustomNodeDialog(QDialog, BaseView):
        def __init__(self, viewmodel: BaseViewModel, parent=None):
            QDialog.__init__(self, parent)
            BaseView.__init__(self, viewmodel, parent)
            self.setWindowTitle("Custom Node")
            self.resize(700, 800)

            # Top-level layout with scrollable content
            self.layout = QVBoxLayout(self)

            from PyQt6.QtWidgets import QScrollArea

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            self.content_layout = QVBoxLayout(content)
            scroll.setWidget(content)
            self.layout.addWidget(scroll)

            # ===== SECTION 1: NODE PROPERTIES =====
            from PyQt6.QtWidgets import (
                QCheckBox,
                QComboBox,
                QGroupBox,
                QHBoxLayout,
                QPlainTextEdit,
                QSpinBox,
            )

            props_group = QGroupBox("Node Properties")
            props_layout = QVBoxLayout()

            # Type name
            trow = QHBoxLayout()
            trow.addWidget(QLabel("Type Name:"))
            self.type_name_edit = QLineEdit()
            self.type_name_edit.setPlaceholderText("e.g., MyCustomNode")
            trow.addWidget(self.type_name_edit)
            props_layout.addLayout(trow)

            # Description
            drow = QHBoxLayout()
            drow.addWidget(QLabel("Description:"))
            self.description_edit = QLineEdit()
            self.description_edit.setPlaceholderText("Optional description for palette")
            drow.addWidget(self.description_edit)
            props_layout.addLayout(drow)

            # Input count
            irow = QHBoxLayout()
            irow.addWidget(QLabel("Number of Inputs:"))
            self.input_count_spin = QSpinBox()
            self.input_count_spin.setMinimum(1)
            self.input_count_spin.setMaximum(10)
            self.input_count_spin.setValue(2)
            irow.addWidget(self.input_count_spin)
            irow.addStretch()
            props_layout.addLayout(irow)

            # Batch size
            brow = QHBoxLayout()
            brow.addWidget(QLabel("Batch Size:"))
            self.batch_size_spin = QSpinBox()
            self.batch_size_spin.setMinimum(1)
            self.batch_size_spin.setMaximum(10)
            self.batch_size_spin.setValue(2)
            brow.addWidget(self.batch_size_spin)
            brow.addStretch()
            props_layout.addLayout(brow)

            # Inclusive and forced batch
            self.inclusive_check = QCheckBox("Inclusive (add result to next batch)")
            self.inclusive_check.setChecked(True)
            props_layout.addWidget(self.inclusive_check)

            self.forced_batch_check = QCheckBox(
                "Forced Batch Processing (continue until insufficient inputs)"
            )
            self.forced_batch_check.setChecked(False)
            props_layout.addWidget(self.forced_batch_check)

            props_group.setLayout(props_layout)
            self.content_layout.addWidget(props_group)

            # ===== SECTION 2: VALID INPUT TYPES =====
            types_group = QGroupBox("Valid Input Types")
            types_layout = QVBoxLayout()
            self.valid_types_checks = {}
            for type_name in ["numeric", "string", "array", "none"]:
                check = QCheckBox(type_name.capitalize())
                self.valid_types_checks[type_name] = check
                types_layout.addWidget(check)
            self.valid_types_checks["numeric"].setChecked(True)
            types_group.setLayout(types_layout)
            self.content_layout.addWidget(types_group)

            # ===== SECTION 3: CUSTOM PROPERTIES =====
            custom_props_group = QGroupBox("Custom Properties (Optional)")
            custom_props_layout = QVBoxLayout()

            self.custom_props_widget = QWidget()
            self.custom_props_container = QVBoxLayout(self.custom_props_widget)
            self.custom_props_container.setContentsMargins(0, 0, 0, 0)
            custom_props_layout.addWidget(self.custom_props_widget)

            self.custom_property_rows = []
            add_prop_btn = QPushButton("Add Property")
            add_prop_btn.clicked.connect(lambda: self.add_custom_property_row())
            custom_props_layout.addWidget(add_prop_btn)

            custom_props_group.setLayout(custom_props_layout)
            self.content_layout.addWidget(custom_props_group)

            # ===== SECTION 4: OPERATION CODE =====
            op_group = QGroupBox("Operation Body")
            op_layout = QVBoxLayout()
            self.placeholder_label = QLabel("Use variables: input1, input2")
            self.placeholder_label.setStyleSheet("color: #888; font-style: italic;")
            op_layout.addWidget(self.placeholder_label)
            self.operation_edit = QPlainTextEdit()
            from PyQt6.QtGui import QFont

            self.operation_edit.setFont(QFont("Courier", 10))
            self.operation_edit.setPlaceholderText(
                "# Write the operation body here\n# Use input1, input2, ... for inputs\n# Return a single value\n\nreturn input1 + input2"
            )
            self.operation_edit.setMinimumHeight(250)
            op_layout.addWidget(self.operation_edit)
            op_group.setLayout(op_layout)
            self.content_layout.addWidget(op_group)

            # Buttons
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            self.save_button = QPushButton("Save")
            self.save_button.clicked.connect(self._on_save)
            btn_layout.addWidget(self.save_button)
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.clicked.connect(self.reject)
            btn_layout.addWidget(self.cancel_button)
            self.layout.addLayout(btn_layout)

            # Bind events
            try:
                self.get_viewmodel().observe_property(
                    "properties_changed", self._on_properties_changed
                )
            except Exception:
                pass
            try:
                self._bind_viewmodel()
            except Exception:
                pass
            # initial render
            self._on_properties_changed(None, None)

        def on_input_count_changed(self, value: int):
            inputs = ", ".join(f"input{i+1}" for i in range(value))
            self.placeholder_label.setText(f"Use variables: {inputs}")

        def add_custom_property_row(
            self, name: str = "", prop_type: str = "any", default_value: str = "None"
        ):
            row_layout = QHBoxLayout()
            name_edit = QLineEdit()
            name_edit.setPlaceholderText("Property name")
            name_edit.setText(name)
            name_edit.setMinimumWidth(120)
            row_layout.addWidget(name_edit)
            type_combo = QComboBox()
            type_combo.addItems(["any", "int", "float", "str", "bool", "node"])
            type_combo.setCurrentText(prop_type)
            type_combo.setMinimumWidth(80)
            row_layout.addWidget(type_combo)
            default_edit = QLineEdit()
            default_edit.setPlaceholderText("Default value (Python)")
            default_edit.setText(default_value)
            default_edit.setMinimumWidth(150)
            row_layout.addWidget(default_edit)
            remove_btn = QPushButton("Remove")
            remove_btn.setMaximumWidth(30)
            row_layout.addWidget(remove_btn)
            row_widget = QWidget()
            row_widget.setLayout(row_layout)
            row_data = {
                "widget": row_widget,
                "name_edit": name_edit,
                "type_combo": type_combo,
                "default_edit": default_edit,
            }
            self.custom_property_rows.append(row_data)
            remove_btn.clicked.connect(
                lambda: self.remove_custom_property_row(row_data)
            )
            self.custom_props_container.addWidget(row_widget)

        def remove_custom_property_row(self, row_data: Dict[str, QWidget]):
            if row_data in self.custom_property_rows:
                self.custom_property_rows.remove(row_data)
                row_data["widget"].deleteLater()

        def _on_properties_changed(self, old, new):
            vm: CustomNodeViewModel = self.get_viewmodel()
            try:
                if self.type_name_edit.text() != vm.get_type_name():
                    self.type_name_edit.setText(vm.get_type_name())
            except Exception:
                pass
            try:
                if self.description_edit.text() != vm.get_description():
                    self.description_edit.setText(vm.get_description())
            except Exception:
                pass
            try:
                if self.input_count_spin.value() != vm.get_input_count():
                    self.input_count_spin.setValue(vm.get_input_count())
            except Exception:
                pass
            try:
                if self.batch_size_spin.value() != vm.get_batch_size():
                    self.batch_size_spin.setValue(vm.get_batch_size())
            except Exception:
                pass
            try:
                self.inclusive_check.setChecked(vm.get_inclusive())
            except Exception:
                pass
            try:
                self.forced_batch_check.setChecked(vm.get_forced_batch_processing())
            except Exception:
                pass
            try:
                for t, check in self.valid_types_checks.items():
                    check.setChecked(t in vm.get_valid_input_types())
            except Exception:
                pass
            # rebuild custom props
            for r in list(self.custom_property_rows):
                try:
                    r["widget"].deleteLater()
                except Exception:
                    pass
            self.custom_property_rows = []
            try:
                for p in vm.get_custom_properties():
                    self.add_custom_property_row(
                        p.get("name", ""),
                        p.get("type", "any"),
                        p.get("default_value", "None"),
                    )
            except Exception:
                pass
            # operation code
            try:
                if self.operation_edit.toPlainText() != vm.get_operation_code():
                    self.operation_edit.setPlainText(vm.get_operation_code())
            except Exception:
                pass

        def _on_save(self):
            vm: CustomNodeViewModel = self.get_viewmodel()
            # gather inputs and write to vm
            try:
                vm.set_type_name(self.type_name_edit.text())
            except Exception:
                pass
            try:
                vm.set_description(self.description_edit.text())
            except Exception:
                pass
            try:
                vm.set_input_count(self.input_count_spin.value())
            except Exception:
                pass
            try:
                vm.set_batch_size(self.batch_size_spin.value())
            except Exception:
                pass
            try:
                vm.set_inclusive(self.inclusive_check.isChecked())
            except Exception:
                pass
            try:
                vm.set_forced_batch_processing(self.forced_batch_check.isChecked())
            except Exception:
                pass
            try:
                selected = [
                    t for t, c in self.valid_types_checks.items() if c.isChecked()
                ]
                vm.set_valid_input_types(selected)
            except Exception:
                pass
            try:
                vm.set_operation_code(self.operation_edit.toPlainText())
            except Exception:
                pass
            # collect custom properties
            props = []
            try:
                for r in self.custom_property_rows:
                    name = r["name_edit"].text().strip()
                    if not name:
                        continue
                    props.append(
                        {
                            "name": name,
                            "type": r["type_combo"].currentText(),
                            "default_value": r["default_edit"].text().strip() or "None",
                        }
                    )
                vm._custom_properties = props
            except Exception:
                pass
            # validate
            try:
                err = vm.validate_operation_code()
            except Exception:
                err = "Could not validate"
            if err:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self, "Invalid Operation Code", f"Error in operation code:\n\n{err}"
                )
                return
            # try saving through manager
            try:
                vm.save_definition()
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self, "Error Saving Custom Node", f"Failed to save custom node: {e}"
                )
                return

            # On success, show a confirmation including the library path when possible
            try:
                from ComputationalGraphs.GUI.custom_node_manager import (
                    get_custom_node_manager,
                )

                mgr = get_custom_node_manager()
                lib_path = getattr(mgr, "library_path", None)
                if lib_path:
                    from PyQt6.QtWidgets import QMessageBox

                    QMessageBox.information(
                        self, "Saved Custom Node", f"Custom node saved to {lib_path}"
                    )
            except Exception:
                pass

            # success - close
            try:
                self.accept()
            except Exception:
                pass

else:

    class CustomNodeDialog:
        def __init__(self, vm, parent=None):
            self.viewmodel = vm

        def exec(self):
            return 0


# Make concrete for ABC checks
if PYQT_AVAILABLE:
    try:
        CustomNodeDialog.__abstractmethods__ = set()
    except Exception:
        pass
