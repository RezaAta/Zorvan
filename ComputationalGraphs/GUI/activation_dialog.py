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
        # Close the underlying dialog and schedule it for deletion. This helps
        # prevent lingering Qt objects across test boundaries which can cause
        # intermittent native crashes on Windows when many GUI tests run.
        try:
            self._dlg.close()
        except Exception:
            pass
        try:
            # Break parent chain first to reduce cross-references
            try:
                self._dlg.setParent(None)
            except Exception:
                pass
            try:
                self._dlg.deleteLater()
            except Exception:
                pass
            # Remove our reference and force a GC to free underlying C++ objects
            try:
                self._dlg = None
            except Exception:
                pass
            try:
                import gc

                gc.collect()
            except Exception:
                pass
            # Process events to let deleteLater complete
            try:
                from PyQt6.QtWidgets import QApplication

                QApplication.processEvents()
            except Exception:
                pass
        except Exception:
            pass
        return None

    def __getattr__(self, name):
        return getattr(self._dlg, name)
