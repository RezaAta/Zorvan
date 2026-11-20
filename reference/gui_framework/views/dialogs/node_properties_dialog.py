"""
NodePropertiesDialog: Dialog to view/edit node properties (name, color, description).
"""

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
    )

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


from ..viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from ...viewmodels.dialogs.node_properties_viewmodel import NodePropertiesViewModel
    from ..base import BaseView

    class NodePropertiesDialog(QDialog, BaseView):
        """Dialog for editing a node's properties."""

        def __init__(self, viewmodel: BaseViewModel, parent=None, target_node=None):
            QDialog.__init__(self, parent)
            BaseView.__init__(self, viewmodel, parent)

            # Backwards compat: tests may expect .viewmodel attribute
            self.viewmodel = viewmodel
            self._target_node = target_node

            self.setWindowTitle("Node Properties")
            self.setModal(True)
            self.resize(360, 240)

            self._setup_ui()
            self._connect_signals()
            # After construction, snapshot the viewmodel state for reset
            try:
                self.get_viewmodel().create_snapshot()
            except Exception:
                pass

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            self.name_edit = QLineEdit()
            form.addRow(QLabel("Name:"), self.name_edit)

            self.color_edit = QLineEdit()
            form.addRow(QLabel("Color (hex):"), self.color_edit)

            self.desc_edit = QTextEdit()
            self.desc_edit.setFixedHeight(80)
            form.addRow(QLabel("Description:"), self.desc_edit)

            layout.addLayout(form)

            # Buttons: Ok, Cancel, Apply, Reset
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
            )
            # Extra action buttons
            self.apply_btn = QPushButton("Apply")
            self.reset_btn = QPushButton("Reset")
            button_box.addButton(self.apply_btn, QDialogButtonBox.ButtonRole.ActionRole)
            button_box.addButton(self.reset_btn, QDialogButtonBox.ButtonRole.ActionRole)

            button_box.accepted.connect(self._on_accept)
            button_box.rejected.connect(self.reject)
            self.apply_btn.clicked.connect(self._on_apply)
            self.reset_btn.clicked.connect(self._on_reset)

            layout.addWidget(button_box)

            # Populate initial state
            self._populate_from_viewmodel()

        def _bind_viewmodel(self):
            # Update UI when properties change in viewmodel
            try:
                vm = self.get_viewmodel()
                vm.observe_property(
                    "properties_changed",
                    lambda old, new: self._populate_from_viewmodel(),
                )
            except Exception:
                pass

            # Validate color live and enable/disable apply/ok accordingly
            try:
                self._validate_color_and_update_buttons()
            except Exception:
                pass

        def _validate_color_and_update_buttons(self):
            vm = self.get_viewmodel()
            color_val = self.color_edit.text()
            valid = vm.validate_color(color_val)
            try:
                self.apply_btn.setEnabled(valid)
            except Exception:
                pass
            # The OK button is part of a QDialogButtonBox - find it and enable/disable
            try:
                for btn in self.findChildren(QDialogButtonBox):
                    for pb in btn.buttons():
                        role = btn.buttonRole(pb)
                        if role == QDialogButtonBox.ButtonRole.AcceptRole:
                            pb.setEnabled(valid)
            except Exception:
                pass

        def _connect_signals(self):
            # Wire UI -> ViewModel immediately (keeps model in sync)
            self.name_edit.textChanged.connect(
                lambda v: self.get_viewmodel().set_name(v)
            )
            # For color, update VM but also validate and update buttons
            self.color_edit.textChanged.connect(
                lambda v: (
                    self.get_viewmodel().set_color(v if v else None),
                    self._validate_color_and_update_buttons(),
                )
            )
            self.desc_edit.textChanged.connect(
                lambda: self.get_viewmodel().set_description(
                    self.desc_edit.toPlainText()
                )
            )

        def _populate_from_viewmodel(self):
            try:
                vm = self.get_viewmodel()
                self.name_edit.setText(vm.get_name())
                self.color_edit.setText(vm.get_color() or "")
                self.desc_edit.setPlainText(vm.get_description())
            except Exception:
                pass

        def _on_accept(self):
            # Final sync (already mostly synced), then accept dialog
            vm = self.get_viewmodel()
            vm.set_name(self.name_edit.text())
            vm.set_color(self.color_edit.text() or None)
            vm.set_description(self.desc_edit.toPlainText())
            # Apply to target node if present
            if self._target_node is not None:
                try:
                    vm.apply_to_node(self._target_node)
                except Exception:
                    pass
            self.accept()

        def _on_apply(self):
            """Apply changes to the underlying node without closing the dialog."""
            vm = self.get_viewmodel()
            vm.set_name(self.name_edit.text())
            vm.set_color(self.color_edit.text() or None)
            vm.set_description(self.desc_edit.toPlainText())

            if self._target_node is not None:
                try:
                    vm.apply_to_node(self._target_node)
                    # Notify the main window status bar if available
                    try:
                        if self.parent() and hasattr(self.parent(), "status_bar"):
                            self.parent().status_bar.showMessage(
                                f"Node '{self._target_node.name}' updated (preview)"
                            )
                    except Exception:
                        pass
                except Exception:
                    pass

        def _on_reset(self):
            """Reset dialog controls to the saved snapshot."""
            try:
                vm = self.get_viewmodel()
                vm.reset_to_snapshot()
                self._populate_from_viewmodel()
                # If a target node exists, also reset it
                if self._target_node is not None:
                    try:
                        vm.apply_to_node(self._target_node)
                        if self.parent() and hasattr(self.parent(), "status_bar"):
                            self.parent().status_bar.showMessage(
                                f"Node '{self._target_node.name}' reset"
                            )
                    except Exception:
                        pass
            except Exception:
                pass

else:
    # Stub for tests without PyQt6
    class NodePropertiesDialog:
        def __init__(self, viewmodel, parent=None):
            self.viewmodel = viewmodel

        def _populate_from_viewmodel(self):
            pass

        def _on_accept(self):
            pass
