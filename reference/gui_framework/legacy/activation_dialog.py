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
        # Close the underlying dialog and schedule it for deletion. In pytest
        # mode, let the test harness flush Qt events instead of forcing an
        # immediate event loop run here, which can interact badly with other
        # widgets created later in the same session.
        try:
            self._dlg.close()
        except Exception:
            pass
        try:
            self._dlg.deleteLater()
        except Exception:
            pass
        try:
            self._dlg = None
        except Exception:
            pass
        try:
            import gc

            gc.collect()
        except Exception:
            pass
        return None

    def __getattr__(self, name):
        return getattr(self._dlg, name)
