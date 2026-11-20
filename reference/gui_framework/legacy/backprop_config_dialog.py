"""
Adapter for BackpropConfigDialog to preserve legacy import path.
"""

try:
    from gui_framework.viewmodels.dialogs.backprop_config_viewmodel import (
        BackpropConfigViewModel,
    )
    from gui_framework.views.dialogs.backprop_config_dialog import (
        BackpropConfigDialog as MVVMBackpropConfigDialog,
    )
except Exception as e:
    raise ImportError("BackpropConfig MVVM components not available: " + str(e))


class BackpropConfigDialog:
    def __init__(self, parent=None):
        # Legacy constructor expected no args and returns a dialog that can be exec'd
        self._vm = BackpropConfigViewModel()
        try:
            self._vm.initialize()
        except Exception:
            pass
        self._dlg = MVVMBackpropConfigDialog(self._vm, parent)

    def exec(self):
        return self._dlg.exec()

    def get_config(self):
        return self._dlg.get_config()

    def close(self):
        return self._dlg.close()

    def __getattr__(self, name):
        return getattr(self._dlg, name)
