"""Activation selection dialog (MVVM) - choose an activation function from a list."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QVBoxLayout

from ...viewmodels.dialogs.activation_viewmodel import ActivationViewModel
from ..base import BaseView


class ActivationDialog(QDialog, BaseView):
    def __init__(self, viewmodel: ActivationViewModel, parent=None):
        QDialog.__init__(self, parent)
        BaseView.__init__(self, viewmodel, parent)
        self._vm = viewmodel
        self.setWindowTitle("Choose Activation")
        self.resize(300, 300)

        self._setup_ui()
        try:
            self.get_viewmodel().initialize()
        except Exception:
            pass
        try:
            self._bind_viewmodel()
        except Exception:
            pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._populate_from_vm()

    def _bind_viewmodel(self):
        vm = self.get_viewmodel()
        vm.observe_property("available", lambda old, new: self._populate_from_vm())
        vm.observe_property("selected", lambda old, new: self._select_in_list(new))

    def _populate_from_vm(self):
        vm = self.get_viewmodel()
        self.list_widget.clear()
        for name in vm.get_available():
            self.list_widget.addItem(name)
        sel = vm.get_selected()
        if sel:
            self._select_in_list(sel)

    def _select_in_list(self, name: str):
        if name is None:
            return
        items = self.list_widget.findItems(name, Qt.MatchFlag.MatchExactly)
        if items:
            self.list_widget.setCurrentItem(items[0])

    def _on_accept(self):
        item = self.list_widget.currentItem()
        if item is not None:
            try:
                self.get_viewmodel().set_selected(item.text())
            except Exception:
                pass
        self.accept()

    def selected(self):
        return self.get_viewmodel().get_selected()
