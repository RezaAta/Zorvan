"""NodeEditorViewModel - Manages editing of node properties and parameters.

This ViewModel is designed to back a NodeEditor dialog view and is testable
without PyQt dependencies.
"""

from dataclasses import dataclass
from typing import Any, Dict

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


@dataclass
class ParameterInfo:
    name: str
    value: Any
    annotation: str = ""


class NodeEditorViewModel(BaseViewModel):
    """ViewModel for the NodeEditor dialog."""

    properties_changed = ObservableProperty("properties_changed", default=0)

    def __init__(self):
        super().__init__()
        self._node = None
        self._name = ""
        self._value = ""
        self._forced_batch = False
        self._incremental = False
        self._parameters: Dict[str, ParameterInfo] = {}
        self._snapshot = None

    def load_from_node(self, node):
        """Load values from a node object (duck-typed)."""
        self._node = node
        self._name = getattr(node, "name", "")
        self._value = str(getattr(node, "value", ""))
        self._forced_batch = bool(getattr(node, "forcedBatchProcessing", False))
        self._incremental = bool(getattr(node, "Incremental", False))

        # Inspect constructor parameters for editable properties
        self._parameters = {}
        try:
            import inspect

            sig = inspect.signature(node.__class__.__init__)
            for p_name, p in sig.parameters.items():
                if p_name in ("self", "name", "value"):
                    continue
                current = getattr(node, p_name, p.default)
                self._parameters[p_name] = ParameterInfo(
                    name=p_name, value=current, annotation=str(p.annotation)
                )
        except Exception:
            # Fallback: no params
            self._parameters = {}

        # Snapshot
        self.create_snapshot()
        self.properties_changed += 1

    def create_snapshot(self):
        self._snapshot = (
            self._name,
            self._value,
            self._forced_batch,
            self._incremental,
            {k: v.value for k, v in self._parameters.items()},
        )

    def reset_to_snapshot(self):
        if self._snapshot is None:
            return
        self._name, self._value, self._forced_batch, self._incremental, params = (
            self._snapshot
        )
        for k, v in params.items():
            if k in self._parameters:
                self._parameters[k].value = v
        self.properties_changed += 1

    # Getters/setters
    def get_name(self):
        return self._name

    def set_name(self, name: str):
        if name != self._name:
            self._name = name
            self.properties_changed += 1

    def get_value(self):
        return self._value

    def set_value(self, value: str):
        if value != self._value:
            self._value = value
            self.properties_changed += 1

    def get_forced_batch(self) -> bool:
        return self._forced_batch

    def set_forced_batch(self, v: bool):
        v = bool(v)
        if v != self._forced_batch:
            self._forced_batch = v
            self.properties_changed += 1

    def get_incremental(self) -> bool:
        return self._incremental

    def set_incremental(self, v: bool):
        v = bool(v)
        if v != self._incremental:
            self._incremental = v
            self.properties_changed += 1

    def get_parameters(self):
        return {k: p.value for k, p in self._parameters.items()}

    def set_parameter(self, name: str, value: Any):
        if name in self._parameters:
            if self._parameters[name].value != value:
                self._parameters[name].value = value
                self.properties_changed += 1

    def apply_to_node(self):
        """Apply current values back to the bound node. Returns True on success."""
        node = self._node
        if node is None:
            return False
        try:
            if hasattr(node, "name"):
                node.name = self._name
            # Try to parse the _value string into a python value if possible
            try:
                node.value = (
                    eval(self._value, {})
                    if isinstance(self._value, str) and self._value.strip() != ""
                    else None
                )
            except Exception:
                # Fallback to raw string
                node.value = self._value

            if hasattr(node, "forcedBatchProcessing"):
                node.forcedBatchProcessing = self._forced_batch
            if hasattr(node, "Incremental"):
                node.Incremental = self._incremental

            for k, p in self._parameters.items():
                try:
                    setattr(node, k, p.value)
                except Exception:
                    pass

            return True
        except Exception:
            return False
