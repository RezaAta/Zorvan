"""
NewGraphDialog: Dialog to create a new computational graph.
"""

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QSpinBox,
        QVBoxLayout,
    )

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


from ..viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from ...viewmodels.dialogs.new_graph_viewmodel import NewGraphViewModel
    from ..base import BaseView

    class NewGraphDialog(QDialog, BaseView):
        """Dialog for creating a new graph."""

        def __init__(self, viewmodel: BaseViewModel, parent=None):
            QDialog.__init__(self, parent)
            BaseView.__init__(self, viewmodel, parent)

            # Backwards compatibility: tests may expect .viewmodel
            self.viewmodel = viewmodel

            self.setWindowTitle("Create New Graph")
            self.setModal(True)
            self.resize(380, 200)

            self._setup_ui()
            self._connect_signals()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            self.name_edit = QLineEdit(self.get_viewmodel().get_name())
            form.addRow(QLabel("Graph Name:"), self.name_edit)

            self.inputs_spin = QSpinBox()
            self.inputs_spin.setMinimum(1)
            self.inputs_spin.setMaximum(1000)
            self.inputs_spin.setValue(self.get_viewmodel().get_num_inputs())
            form.addRow(QLabel("Number of Inputs:"), self.inputs_spin)

            self.outputs_spin = QSpinBox()
            self.outputs_spin.setMinimum(1)
            self.outputs_spin.setMaximum(1000)
            self.outputs_spin.setValue(self.get_viewmodel().get_num_outputs())
            form.addRow(QLabel("Number of Outputs:"), self.outputs_spin)

            self.type_combo = QComboBox()
            self.type_combo.addItem("MLP", "MLP")
            self.type_combo.addItem("ANFIS", "ANFIS")
            idx = 0 if self.get_viewmodel().get_graph_type() == "MLP" else 1
            self.type_combo.setCurrentIndex(idx)
            form.addRow(QLabel("Graph Type:"), self.type_combo)

            layout.addLayout(form)

            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(self._on_accept)
            button_box.rejected.connect(self.reject)
            layout.addWidget(button_box)

        def _bind_viewmodel(self):
            try:
                vm = self.get_viewmodel()
                vm.observe_property(
                    "properties_changed",
                    lambda old, new: self._populate_from_viewmodel(),
                )
            except Exception:
                pass

        def _connect_signals(self):
            self.name_edit.textChanged.connect(
                lambda v: self.get_viewmodel().set_name(v)
            )
            self.inputs_spin.valueChanged.connect(
                lambda v: self.get_viewmodel().set_num_inputs(v)
            )
            self.outputs_spin.valueChanged.connect(
                lambda v: self.get_viewmodel().set_num_outputs(v)
            )
            self.type_combo.currentIndexChanged.connect(
                lambda i: self.get_viewmodel().set_graph_type(
                    self.type_combo.itemData(i)
                )
            )

        def _populate_from_viewmodel(self):
            try:
                vm = self.get_viewmodel()
                self.name_edit.setText(vm.get_name())
                self.inputs_spin.setValue(vm.get_num_inputs())
                self.outputs_spin.setValue(vm.get_num_outputs())
                self.type_combo.setCurrentIndex(
                    0 if vm.get_graph_type() == "MLP" else 1
                )
            except Exception:
                pass

        def _on_accept(self):
            vm = self.get_viewmodel()
            # Ensure values are synced
            vm.set_name(self.name_edit.text())
            vm.set_num_inputs(self.inputs_spin.value())
            vm.set_num_outputs(self.outputs_spin.value())
            vm.set_graph_type(self.type_combo.itemData(self.type_combo.currentIndex()))

            # Create graph representation and accept
            vm.create_graph()
            self.accept()

else:

    class NewGraphDialog:
        def __init__(self, viewmodel, parent=None):
            self.viewmodel = viewmodel

        def _on_accept(self):
            pass
