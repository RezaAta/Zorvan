"""
Inspector ViewModel for node property inspection and editing.

Pure-Python, testable logic to inspect the currently selected node and
allow editing properties like name, color, and custom attributes. It
observes a CanvasViewModel for selection changes.
"""

from typing import Any, Dict, Optional

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class InspectorViewModel(BaseViewModel):
    selected_node_id = ObservableProperty("selected_node_id", default=None)
    properties_changed = ObservableProperty("properties_changed", default=0)

    def __init__(self, canvas_vm=None):
        super().__init__()
        self.canvas_vm = canvas_vm
        self._selected_props: Dict[str, Any] = {}

    def initialize(self):
        """Start observing canvas selection changes."""
        if self.canvas_vm:
            # Observe canvas nodes_changed to keep selection in sync
            self.canvas_vm.observe_property(
                "nodes_changed", self._on_canvas_nodes_changed
            )
        self._mark_initialized()

    def cleanup(self):
        if self.canvas_vm:
            self.canvas_vm.unobserve_property(
                "nodes_changed", self._on_canvas_nodes_changed
            )

    def _on_canvas_nodes_changed(self, old, new):
        # Update selected node information when canvas signals change
        selected = self.canvas_vm.get_selected_nodes()
        if selected:
            node_id = selected[0]
        else:
            node_id = None

        if node_id != self.selected_node_id:
            self.selected_node_id = node_id
            self._load_properties_for(node_id)

    def _load_properties_for(self, node_id: Optional[str]):
        self._selected_props = {}
        if not node_id:
            self.properties_changed += 1
            return

        node_state = self.canvas_vm.get_node(node_id)
        if not node_state:
            self.properties_changed += 1
            return

        # Base properties from render state
        self._selected_props["name"] = node_state.name
        self._selected_props["x"] = node_state.x
        self._selected_props["y"] = node_state.y
        self._selected_props["color"] = node_state.color
        self._selected_props["is_active"] = node_state.is_active

        # Try to add underlying graph attributes if available
        if self.canvas_vm._graph:
            graph_nodes = {n.name: n for n in self.canvas_vm._graph.nodes}
            if node_state.node_id in graph_nodes:
                graph_node = graph_nodes[node_state.node_id]
                # Add any user-defined attributes (non-callable, not dunder)
                for attr in dir(graph_node):
                    if attr.startswith("__"):
                        continue
                    if attr in ("name", "predecessors", "x", "y"):
                        continue
                    try:
                        val = getattr(graph_node, attr)
                        if not callable(val):
                            self._selected_props[attr] = val
                    except Exception:
                        pass

        self.properties_changed += 1

    def get_properties(self) -> Dict[str, Any]:
        return dict(self._selected_props)

    def set_property(self, prop_name: str, value: Any) -> bool:
        """Set a property on the selected node; returns True on success."""
        node_id = self.selected_node_id
        if not node_id:
            return False

        node_state = self.canvas_vm.get_node(node_id)
        if not node_state:
            return False

        # Update render state where applicable
        if prop_name in ("name", "x", "y", "color", "is_active"):
            setattr(node_state, prop_name, value)
            self.canvas_vm.nodes_changed += 1
            self._load_properties_for(node_id)
            return True

        # Otherwise try to set attribute on underlying graph node
        if self.canvas_vm._graph:
            graph_nodes = {n.name: n for n in self.canvas_vm._graph.nodes}
            if node_id in graph_nodes:
                try:
                    setattr(graph_nodes[node_id], prop_name, value)
                    self._load_properties_for(node_id)
                    return True
                except Exception:
                    return False

        return False
