"""Adapter for Learning Rate dialog (legacy import path)."""

try:
    from gui_framework.viewmodels.dialogs.learning_rate_viewmodel import (
        LearningRateViewModel,
    )
    from gui_framework.views.dialogs.learning_rate_dialog import (
        LearningRateDialog as MVVMLearningRateDialog,
    )
except Exception as e:
    raise ImportError("LearningRate MVVM components not available: " + str(e))


class LearningRateDialog:
    def __init__(self, node=None, parent=None):
        # node optional; when provided, viewmodel will be initialized from node value
        initial = None
        if node is not None:
            if hasattr(node, "learning_rate"):
                initial = getattr(node, "learning_rate")
            elif hasattr(node, "value"):
                initial = getattr(node, "value")
        self._vm = LearningRateViewModel(value=initial)
        try:
            self._vm.initialize()
        except Exception:
            pass
        self._dlg = MVVMLearningRateDialog(self._vm, parent)
        self._node = node

    def exec(self):
        return self._dlg.exec()

    def apply_to_node(self):
        if self._node is not None:
            return self._dlg.apply_to_node(self._node)
        return False

    def get_value(self):
        return self._dlg.get_value()

    def close(self):
        return self._dlg.close()

    def __getattr__(self, name):
        return getattr(self._dlg, name)
