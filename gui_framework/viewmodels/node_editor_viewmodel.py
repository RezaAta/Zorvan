"""
Node Editor ViewModel: provides an editable representation of a node's properties
for use in dialogs. Pure Python and testable.
"""

import ast
from typing import Any, Dict, Optional

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty
from zorvan.Nodes.computation_type import to_value


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
                    # Accept simple types and lightweight containers so they can be
                    # edited in the dialog. This includes dicts which are used by
                    # some nodes for small configs.
                    if isinstance(val, (int, float, bool, str, list, tuple, dict)):
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
            # Expose computation type under a consistent key (string for UI)
            raw_ct = getattr(node, "computationType", None)
            try:
                self._props["computationType"] = (
                    to_value(raw_ct) if raw_ct is not None else None
                )
            except Exception:
                self._props["computationType"] = str(raw_ct)
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
            # If editor attempted to set an empty value, ignore the assignment to avoid
            # accidentally clearing an existing numeric value. This preserves the
            # authoritative node.value unless an explicit clear action is provided.
            if prop_name == "value" and (value is None or value == ""):
                # Keep internal viewmodel property consistent with the node's current value
                self._props[prop_name] = self._props.get(
                    prop_name, getattr(self._node, "value", None)
                )
                # Do not change node.value or node.user_locked_value on empty assignment
                self.properties_changed += 1
                return True

            setattr(self._node, prop_name, value)
            self._props[prop_name] = value
            # If user set the 'value' property via the editor, treat it as an explicit edit
            # and mark the node as user-locked so automatic resets won't overwrite it.
            if prop_name == "value":
                try:
                    # Only set user_locked_value when a non-empty value was provided
                    self._node.user_locked_value = True
                except Exception:
                    pass
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

        Special case: an empty string preserves the node's current value and lock state.
        """
        try:
            # Empty input means keep the existing value and lock state unchanged.
            if isinstance(value, str) and value == "":
                # Keep the viewmodel in sync with the node's current value
                self._props["value"] = getattr(self._node, "value", "")
                self.properties_changed += 1
                return True

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
        """Set a parameter on the node.

        If the original parameter value was a list or tuple and the editor passed a
        string (from a QLineEdit), attempt to parse it safely into a list using
        ast.literal_eval. If parsing fails, fall back to comma-splitting and
        attempt to literal-evaluate each item.
        """
        # If this property was previously a list/tuple, try to convert string
        # representations back to a list to preserve type expectations in node code.
        orig = self._props.get(name, None)
        if isinstance(orig, (list, tuple)) and isinstance(value, str):
            # Try safe literal eval first
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, (list, tuple)):
                    return self.set_property(name, list(parsed))
            except Exception:
                # Fall through to comma-split fallback
                pass

            # Fallback: split on commas and attempt to parse each item
            parts = [p.strip() for p in value.split(",") if p.strip() != ""]
            parsed_parts = []
            for p in parts:
                try:
                    parsed_parts.append(ast.literal_eval(p))
                except Exception:
                    parsed_parts.append(p)
            return self.set_property(name, parsed_parts)

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
