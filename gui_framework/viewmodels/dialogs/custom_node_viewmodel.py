"""CustomNodeViewModel - manages editing of Custom Node parameters and metadata."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


@dataclass
class ParamInfo:
    name: str
    value: Any
    annotation: str = ""


class CustomNodeViewModel(BaseViewModel):
    """ViewModel for editing Custom Node definitions in MVVM dialogs.

    This ViewModel mirrors the legacy CustomNodeDefinition fields and offers
    helpers to load/save definitions and validate operation code. It is
    intentionally simple and delegates persistence to the existing
    CustomNodeManager.
    """

    properties_changed = ObservableProperty("properties_changed", default=0)

    def __init__(self, definition: Optional[object] = None):
        super().__init__()
        # Core fields mirroring CustomNodeDefinition
        self._node_ref = None
        self._type_name: str = ""
        self._input_count: int = 2
        self._batch_size: int = 2
        self._inclusive: bool = True
        self._forced_batch_processing: bool = False
        self._valid_input_types: List[str] = ["numeric"]
        self._operation_code: str = "return input1 + input2"
        self._description: str = ""
        # Custom properties list of dicts: {name, type, default_value}
        self._custom_properties: List[Dict[str, Any]] = []
        # Simple param map for UI payloads (legacy compatibility)
        self._params: Dict[str, ParamInfo] = {}

        if definition is not None:
            # Prefer node-like objects with params; fall back to definition-like
            # objects used by the custom-node editor.
            if hasattr(definition, "params") and not hasattr(definition, "type_name"):
                self.load_from_node(definition)
            else:
                try:
                    self.load_from_definition(definition)
                except Exception:
                    self.load_from_node(definition)

    def initialize(self):
        return True

    def cleanup(self):
        return True

    def load_from_definition(self, d):
        """Load fields from a CustomNodeDefinition-like object."""
        try:
            self._node_ref = None
            self._type_name = getattr(d, "type_name", getattr(d, "name", ""))
            self._input_count = int(getattr(d, "input_count", 2))
            self._batch_size = int(getattr(d, "batch_size", 2))
            self._inclusive = bool(getattr(d, "inclusive", True))
            self._forced_batch_processing = bool(
                getattr(d, "forced_batch_processing", False)
            )
            self._valid_input_types = list(getattr(d, "valid_input_types", ["numeric"]))
            self._operation_code = getattr(d, "operation_code", self._operation_code)
            self._description = str(getattr(d, "description", ""))
            self._custom_properties = list(getattr(d, "custom_properties", []))
        except Exception:
            # Fallback to safe defaults
            self.__init__()
        self.properties_changed += 1

    def load_from_node(self, node):
        """Compatibility loader for node-like objects with params and name/description."""
        self._node_ref = node
        self._type_name = getattr(node, "name", "")
        self._description = str(getattr(node, "description", ""))
        self._params = {}
        try:
            attrs = getattr(node, "params", {})
            for k, v in dict(attrs).items():
                self._params[k] = ParamInfo(
                    name=k, value=v, annotation=type(v).__name__
                )
        except Exception:
            self._params = {}
        self.properties_changed += 1

    # Accessors and mutators for all fields
    def get_name(self) -> str:
        return self.get_type_name()

    def set_name(self, v: str):
        self.set_type_name(v)

    def get_type_name(self) -> str:
        return self._type_name

    def set_type_name(self, v: str):
        if v != self._type_name:
            self._type_name = v
            self.properties_changed += 1

    def get_input_count(self) -> int:
        return self._input_count

    def set_input_count(self, v: int):
        if v != self._input_count:
            self._input_count = int(v)
            self.properties_changed += 1

    def get_batch_size(self) -> int:
        return self._batch_size

    def set_batch_size(self, v: int):
        if v != self._batch_size:
            self._batch_size = int(v)
            self.properties_changed += 1

    def get_inclusive(self) -> bool:
        return self._inclusive

    def set_inclusive(self, v: bool):
        if v != self._inclusive:
            self._inclusive = bool(v)
            self.properties_changed += 1

    def get_forced_batch_processing(self) -> bool:
        return self._forced_batch_processing

    def set_forced_batch_processing(self, v: bool):
        if v != self._forced_batch_processing:
            self._forced_batch_processing = bool(v)
            self.properties_changed += 1

    def get_valid_input_types(self) -> List[str]:
        return list(self._valid_input_types)

    def set_valid_input_types(self, types: List[str]):
        self._valid_input_types = list(types)
        self.properties_changed += 1

    def get_operation_code(self) -> str:
        return self._operation_code

    def set_operation_code(self, code: str):
        if code != self._operation_code:
            self._operation_code = code
            self.properties_changed += 1

    def get_description(self) -> str:
        return self._description

    def set_description(self, d: str):
        if d != self._description:
            self._description = d
            self.properties_changed += 1

    def apply_to_node(self) -> bool:
        """Apply the current view-model values back to the loaded node object."""
        node = self._node_ref
        if node is None:
            return False

        try:
            node.name = self._type_name
        except Exception:
            pass
        try:
            node.description = self._description
        except Exception:
            pass
        try:
            if not hasattr(node, "params") or node.params is None:
                node.params = {}
            for key, param in self._params.items():
                node.params[key] = param.value
        except Exception:
            pass
        return True

    def get_custom_properties(self) -> List[Dict[str, Any]]:
        return list(self._custom_properties)

    def add_custom_property(
        self, name: str, ptype: str = "any", default_value: str = "None"
    ):
        self._custom_properties.append(
            {"name": name, "type": ptype, "default_value": default_value}
        )
        self.properties_changed += 1

    def remove_custom_property(self, name: str):
        self._custom_properties = [
            p for p in self._custom_properties if p.get("name") != name
        ]
        self.properties_changed += 1

    def get_definition(self):
        """Return a CustomNodeDefinition-like object built from current fields."""
        try:
            from gui_framework.legacy import CustomNodeDefinition

            if CustomNodeDefinition is not None:
                return CustomNodeDefinition(
                    type_name=self._type_name,
                    input_count=self._input_count,
                    batch_size=self._batch_size,
                    inclusive=self._inclusive,
                    forced_batch_processing=self._forced_batch_processing,
                    valid_input_types=list(self._valid_input_types) or ["numeric"],
                    operation_code=self._operation_code,
                    description=self._description,
                    custom_properties=list(self._custom_properties),
                )
        except Exception:
            # Return a minimal dict fallback
            return {
                "type_name": self._type_name,
                "input_count": self._input_count,
                "batch_size": self._batch_size,
                "inclusive": self._inclusive,
                "forced_batch_processing": self._forced_batch_processing,
                "valid_input_types": list(self._valid_input_types) or ["numeric"],
                "operation_code": self._operation_code,
                "description": self._description,
                "custom_properties": list(self._custom_properties),
            }

    def validate_operation_code(self) -> Optional[str]:
        """Validate the currently-set operation code using CustomNodeDefinition helper."""
        try:
            d = self.get_definition()
            return d.validate_operation_code()
        except Exception:
            return "Could not validate operation code"

    def save_definition(self) -> bool:
        """Persist the current definition via CustomNodeManager.

        Returns True on success, raises on failure.
        """
        definition = self.get_definition()
        try:
            from gui_framework.legacy import (
                get_custom_node_manager_safe as get_custom_node_manager,
            )

            mgr = get_custom_node_manager()
            if mgr is not None:
                return mgr.add_definition(definition)
            return False
        except Exception as e:
            raise

    # Small compatibility layer for legacy param map
    def get_params(self):
        return {k: p.value for k, p in self._params.items()}

    def set_param(self, name: str, value: Any):
        if name in self._params and self._params[name].value != value:
            self._params[name].value = value
            self.properties_changed += 1
