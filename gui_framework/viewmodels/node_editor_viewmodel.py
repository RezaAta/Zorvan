"""
Node Editor ViewModel: provides an editable representation of a node's properties
for use in dialogs. Pure Python and testable.
"""

import ast
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

        # Provide a read-only 'type' property exposing the node's class name
        try:
            self._props["type"] = type(node).__name__
        except Exception:
            pass

        # Additional read-only details shown in 'More details' panel
        try:
            gp = getattr(node, "gui_pos", None)
            # Format gui_pos as "x: <x>, y: <y>" when possible
            formatted_gp = None
            if gp is not None:
                try:
                    if isinstance(gp, (list, tuple)) and len(gp) == 2:
                        formatted_gp = f"x: {gp[0]}, y: {gp[1]}"
                    elif isinstance(gp, dict) and "x" in gp and "y" in gp:
                        formatted_gp = f"x: {gp['x']}, y: {gp['y']}"
                    elif hasattr(gp, "x") and hasattr(gp, "y"):
                        # Try call-style (e.g., QPoint)
                        try:
                            formatted_gp = f"x: {gp.x()}, y: {gp.y()}"
                        except Exception:
                            formatted_gp = (
                                f"x: {getattr(gp, 'x', '')}, y: {getattr(gp, 'y', '')}"
                            )
                    else:
                        formatted_gp = str(gp)
                except Exception:
                    formatted_gp = str(gp)
            self._props["gui_pos"] = formatted_gp
        except Exception:
            pass
        try:
            # Expose computation type under a consistent key
            self._props["computationType"] = getattr(node, "computationType", None)
        except Exception:
            pass
        try:
            self._props["batchSize"] = getattr(node, "batchSize", None)
        except Exception:
            pass
        try:
            self._props["id"] = getattr(node, "id", None)
        except Exception:
            pass
        try:
            self._props["inputCount"] = getattr(node, "inputCount", None)
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

    # Compatibility helpers expected by MVVM dialogs
    def get_name(self) -> str:
        return self._props.get("name", self.node_id)

    def set_name(self, name: str) -> bool:
        return self.set_property("name", name)

    def get_value(self):
        return self._props.get("value", "")

    def set_value(self, value) -> bool:
        """Set the node's value from either a Python object or a string representation.
        If a string is provided, attempt safe literal parsing with ast.literal_eval.
        """
        try:
            # If value is a string, attempt to parse literal (safe)
            if isinstance(value, str):
                try:
                    parsed = ast.literal_eval(value)
                except Exception:
                    # Treat as raw string if parsing fails
                    parsed = value
            else:
                parsed = value
            return self.set_property("value", parsed)
        except Exception:
            return False

    def get_parameters(self) -> dict:
        # Return parameter-like properties (exclude header fields)
        excluded = {
            "name",
            "value",
            "description",
            "forcedBatchProcessing",
            "type",
            "gui_pos",
            "computationType",
            "batchSize",
            "id",
            "inputCount",
        }
        return {k: v for k, v in self._props.items() if k not in excluded}

    def set_parameter(self, name: str, value) -> bool:
        return self.set_property(name, value)

    def apply_to_node(self) -> bool:
        # NodeEditorDialog expects this to exist; properties are already applied in set_property
        return True

    def get_forced_batch(self):
        return self._props.get("forcedBatchProcessing", None)

    def set_forced_batch(self, val: bool) -> bool:
        return self.set_property("forcedBatchProcessing", bool(val))

    def get_incremental(self) -> bool:
        return bool(self._props.get("incremental", False))

    def set_incremental(self, val: bool) -> bool:
        return self.set_property("incremental", bool(val))
