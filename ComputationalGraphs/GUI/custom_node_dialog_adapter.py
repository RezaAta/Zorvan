"""Lightweight adapter exposing MVVM-based CustomNodeDialog for tests/development.

This is a transitional adapter that allows constructing the MVVM dialog using a
simple `node`-like object. It does not replace the legacy `CustomNodeDialog`
implementation in this module; it exists alongside it to ease migration and
testing.
"""

try:
    from gui_framework.viewmodels.dialogs.custom_node_viewmodel import (
        CustomNodeViewModel,
    )
    from gui_framework.views.dialogs.custom_node_dialog import (
        CustomNodeDialog as MVVMCustomNodeDialog,
    )
except Exception as e:
    raise ImportError("MVVM CustomNode components not available: " + str(e))


class CustomNodeDialogAdapter:
    """Adapter that accepts a simple dict-like node (or any duck-typed object)
    and constructs a `CustomNodeViewModel` and MVVM dialog.
    """

    def __init__(self, node_like, parent=None):
        # Build a minimal shim that the VM understands
        class Shim:
            pass

        shim = Shim()
        shim.name = getattr(node_like, "name", getattr(node_like, "type_name", ""))
        shim.description = getattr(node_like, "description", "")
        # Expect node_like.params or node_like.custom_properties
        params = {}
        if hasattr(node_like, "params") and isinstance(node_like.params, dict):
            params = dict(node_like.params)
        elif hasattr(node_like, "custom_properties"):
            # Convert list of {name,type,default_value} to a dict
            for p in getattr(node_like, "custom_properties") or []:
                params[p.get("name")] = p.get("default_value", "None")
        shim.params = params

        self._vm = CustomNodeViewModel(shim)
        try:
            self._vm.initialize()
        except Exception:
            pass
        self._dlg = MVVMCustomNodeDialog(self._vm, parent)
        self.node_like = node_like

    def exec(self):
        return self._dlg.exec()

    def close(self):
        return self._dlg.close()

    def __getattr__(self, name):
        return getattr(self._dlg, name)
