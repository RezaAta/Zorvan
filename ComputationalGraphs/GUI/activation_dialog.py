"""Legacy adapter for ActivationDialog — preserves old import path."""

try:
    from gui_framework.viewmodels.dialogs.activation_viewmodel import (
        ActivationViewModel,
    )
    from gui_framework.views.dialogs.activation_dialog import (
        ActivationDialog as MVVMActivationDialog,
    )
except Exception as e:
    raise ImportError("Activation MVVM components not available: " + str(e))


class ActivationDialog:
    def __init__(self, parent=None, available=None, selected=None):
        # Support legacy constructor signature: ActivationDialog(parent, available, selected)
        if available is None:
            available = ["Sigmoid", "ReLU", "Linear", "Tanh"]
        self._vm = ActivationViewModel(available=available, selected=selected)
        try:
            self._vm.initialize()
        except Exception:
            pass
        self._dlg = MVVMActivationDialog(self._vm, parent)

    def exec(self):
        return self._dlg.exec()

    def selected(self):
        return self._dlg.selected()

    def close(self):
        return self._dlg.close()

    def __getattr__(self, name):
        return getattr(self._dlg, name)
