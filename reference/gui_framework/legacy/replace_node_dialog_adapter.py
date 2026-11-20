"""Adapter for legacy ReplaceNodeDialog - delegates to MVVM dialog."""

try:
    from gui_framework.viewmodels.dialogs.replace_node_viewmodel import (
        ReplaceNodeViewModel,
    )
    from gui_framework.views.dialogs.replace_node_dialog import (
        ReplaceNodeDialog as MVVMReplaceNodeDialog,
    )
except Exception as e:
    raise ImportError("MVVM ReplaceNode components not available: " + str(e))


class ReplaceNodeDialog:
    def __init__(self, parent=None):
        # Construct VM and load registry
        self._vm = ReplaceNodeViewModel()
        try:
            # Try to import registry getter from existing module
            from .node_registry import get_node_categories

            self._vm.load_from_registry(get_node_categories)
        except Exception:
            # leave empty categories
            pass
        try:
            self._vm.initialize()
        except Exception:
            pass
        self._dlg = MVVMReplaceNodeDialog(self._vm, parent)

    def exec(self):
        return self._dlg.exec()

    def selected_type(self):
        return self._dlg.selected_type()

    def close(self):
        return self._dlg.close()

    def __getattr__(self, name):
        return getattr(self._dlg, name)
