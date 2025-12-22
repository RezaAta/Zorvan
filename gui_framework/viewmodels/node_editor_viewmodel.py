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

        # Allow nodes to explicitly declare editable properties
        editable = getattr(node, "editable_properties", None)
        if editable is not None:
            try:
                for name in editable:
                    try:
                        self._props[name] = getattr(node, name)
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            # Conservative automatic discovery: include only simple, non-private attributes
            for attr in dir(node):
                if attr.startswith("_"):
                    continue
                if attr in ("predecessors", "successors", "graph"):
                    continue
                try:
                    val = getattr(node, attr)
                    if callable(val):
                        continue
                    # Accept simple types only to avoid exposing complex runtime state
                    if isinstance(val, (int, float, bool, str, list, tuple)):
                        self._props[attr] = val
                except Exception:
                    pass

        # Actions: nodes may provide editor_actions dict or expose known helper methods
        self._actions = {}
        try:
            explicit = getattr(node, "editor_actions", None)
            if isinstance(explicit, dict):
                for label, handler in explicit.items():
                    try:
                        if isinstance(handler, str) and hasattr(node, handler):
                            self._actions[label] = getattr(node, handler)
                        elif callable(handler):
                            self._actions[label] = handler
                    except Exception:
                        pass
            else:
                # Common helper method names to expose
                for name in (
                    "regenerate_population",
                    "get_population_stats",
                    "reinitialize",
                    "reinitialize_weight",
                    "randomize",
                ):
                    if hasattr(node, name) and callable(getattr(node, name)):
                        self._actions[name] = getattr(node, name)
        except Exception:
            self._actions = {}

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

    def get_actions(self):
        try:
            return dict(self._actions)
        except Exception:
            return {}

    def call_action(self, name: str):
        try:
            if name in self._actions:
                return self._actions[name]()
        except Exception:
            pass
        return None
