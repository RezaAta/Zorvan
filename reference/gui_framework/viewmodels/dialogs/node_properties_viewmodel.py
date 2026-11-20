from typing import Optional

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class NodePropertiesViewModel(BaseViewModel):
    """ViewModel for Node Properties dialog.

    Exposes simple node properties for editing in a dialog.
    """

    properties_changed = ObservableProperty("properties_changed", default=0)

    def __init__(
        self,
        node_id: str = None,
        name: str = "",
        color: Optional[str] = None,
        description: str = "",
    ):
        super().__init__()
        self._node_id = node_id
        self._name = name
        self._color = color
        self._description = description

    # Simple getters
    def get_node_id(self) -> Optional[str]:
        return self._node_id

    def get_name(self) -> str:
        return self._name

    def get_color(self) -> Optional[str]:
        return self._color

    def get_description(self) -> str:
        return self._description

    # Setters that notify observers
    def set_name(self, name: str):
        if name != self._name:
            self._name = name
            self.properties_changed += 1

    def set_color(self, color: Optional[str]):
        if color != self._color:
            self._color = color
            self.properties_changed += 1

    def set_description(self, description: str):
        if description != self._description:
            self._description = description
            self.properties_changed += 1

    # Convenience: load from a simple node object/dict
    def load_from_node(self, node):
        try:
            self._node_id = getattr(node, "id", None) or getattr(node, "name", None)
            self._name = getattr(node, "name", self._name)
            self._color = getattr(node, "color", self._color)
            self._description = getattr(node, "description", self._description)
            # Fire initial change to notify listeners
            self.properties_changed += 1
            # Create a snapshot to allow reset/preview
            try:
                self.create_snapshot()
            except Exception:
                pass
        except Exception:
            pass

    # Apply changes back to a node (duck-typed)
    def apply_to_node(self, node):
        try:
            if hasattr(node, "name"):
                node.name = self._name
            if hasattr(node, "color"):
                node.color = self._color
            if hasattr(node, "description"):
                node.description = self._description
            return True
        except Exception:
            return False

    # Snapshot / reset support for dialog preview
    def create_snapshot(self):
        """Create a snapshot of current properties to allow reset."""
        self._snapshot = (self._name, self._color, self._description)

    def reset_to_snapshot(self):
        """Reset properties to the last snapshot and notify observers."""
        if hasattr(self, "_snapshot") and self._snapshot is not None:
            self._name, self._color, self._description = self._snapshot
            self.properties_changed += 1

    @staticmethod
    def validate_color(value: str) -> bool:
        """Validate hex color string in the form #RRGGBB (case-insensitive)."""
        if not value:
            return True
        try:
            import re

            return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", value.strip()))
        except Exception:
            return False

    # Lifecycle hooks (required by BaseViewModel)
    def initialize(self) -> None:
        # No-op for simple dialog VM
        self._mark_initialized()

    def cleanup(self) -> None:
        # No resources to release
        pass
