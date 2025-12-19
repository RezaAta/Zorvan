"""
Node Editor ViewModel: provides an editable representation of a node's properties
for use in dialogs. Pure Python and testable.
"""

from typing import Any, Dict, Optional

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class NodeEditorViewModel(BaseViewModel):
    node_id = ObservableProperty("node_id", default=None)
    properties_changed = ObservableProperty("properties_changed", default=0)

    def __init__(self, node=None):
        super().__init__()
        self._node = node
        self._props: Dict[str, Any] = {}

    def initialize(self):
        self._mark_initialized()
        if self._node:
            self.load_node(self._node)

    def cleanup(self):
        self._node = None
        self._props = {}

    def load_node(self, node):
        self._node = node
        self.node_id = getattr(node, "name", str(node))
        self._props = {}
        for attr in dir(node):
            if attr.startswith("__"):
                continue
            if attr in ("predecessors",):
                continue
            try:
                val = getattr(node, attr)
                if not callable(val):
                    self._props[attr] = val
            except Exception:
                pass
        self.properties_changed += 1

    def get_properties(self) -> Dict[str, Any]:
        return dict(self._props)

    def set_property(self, prop_name: str, value: Any) -> bool:
        if not self._node:
            return False
        try:
            setattr(self._node, prop_name, value)
            self._props[prop_name] = value
            self.properties_changed += 1
            return True
        except Exception:
            return False
