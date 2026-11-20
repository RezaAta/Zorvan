"""
Canvas ViewModel - Pure Python logic for graph canvas rendering.

Manages the state and logic for the computational graph canvas without
any PyQt dependencies. This includes node/edge rendering state, zoom/pan
state, and selection state.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from gui_framework.events.bus import Event, EventType
from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


@dataclass
class NodeRenderState:
    """State for rendering a single node."""

    node_id: str
    name: str
    x: float
    y: float
    radius: float = 40.0
    color: Optional[str] = None  # Hex color string, None for default
    is_selected: bool = False
    is_active: bool = False
    is_compressed: bool = False
    is_abstract: bool = False
    node_count: Optional[int] = None  # For compressed/abstract nodes


@dataclass
class EdgeRenderState:
    """State for rendering a single edge."""

    edge_id: str
    source_node_id: str
    target_node_id: str
    is_selected: bool = False


@dataclass
class CanvasViewport:
    """Viewport state for canvas zoom/pan."""

    center_x: float = 0.0
    center_y: float = 0.0
    zoom_level: float = 1.0
    min_zoom: float = 0.1
    max_zoom: float = 5.0

    def zoom_in(self, factor: float = 1.2):
        """Zoom in by factor."""
        self.zoom_level = min(self.zoom_level * factor, self.max_zoom)

    def zoom_out(self, factor: float = 1.2):
        """Zoom out by factor."""
        self.zoom_level = max(self.zoom_level / factor, self.min_zoom)

    def pan(self, dx: float, dy: float):
        """Pan the viewport."""
        self.center_x += dx
        self.center_y += dy

    def reset(self):
        """Reset viewport to default."""
        self.center_x = 0.0
        self.center_y = 0.0
        self.zoom_level = 1.0


class CanvasViewModel(BaseViewModel):
    """
    ViewModel for the computational graph canvas.

    Manages rendering state for nodes and edges, viewport state (zoom/pan),
    and provides read-only access to the graph structure for rendering.

    This is the "Core" version focused on rendering only. Interaction
    (drag, select, connect) will be added in Stage 2.
    """

    # Observable properties
    viewport_changed = ObservableProperty(
        "viewport_changed", default=0
    )  # Counter to trigger updates
    nodes_changed = ObservableProperty("nodes_changed", default=0)
    edges_changed = ObservableProperty("edges_changed", default=0)

    def __init__(self, graph=None):
        """
        Initialize canvas view-model.

        Args:
            graph: Optional ComputationalGraph instance
        """
        super().__init__()
        self._graph = graph
        self._nodes: Dict[str, NodeRenderState] = {}
        self._edges: Dict[str, EdgeRenderState] = {}
        self._viewport = CanvasViewport()
        self._selected_nodes: Set[str] = set()
        self._selected_edges: Set[str] = set()

    def initialize(self):
        """Called when View is shown."""
        print("[CanvasViewModel] Initialized")
        if self._graph:
            self.load_graph(self._graph)
        # Mark as initialized for frameworks/tests that may call initialize() directly
        try:
            self._mark_initialized()
        except Exception:
            pass

    def cleanup(self):
        """Called when View is closed."""
        print("[CanvasViewModel] Cleanup")
        self._nodes.clear()
        self._edges.clear()
        self._selected_nodes.clear()
        self._selected_edges.clear()

    # Graph management

    def load_graph(self, graph):
        """
        Load a computational graph for rendering.

        Args:
            graph: ComputationalGraph instance
        """
        self._graph = graph
        self._nodes.clear()
        self._edges.clear()
        self._selected_nodes.clear()
        self._selected_edges.clear()

        # Create render state for each node
        for node in graph.nodes:
            # Determine if node is compressed or abstract using duck typing
            # Check if node has these specific classes by name to avoid import dependencies
            node_class_name = type(node).__name__
            is_compressed = node_class_name == "CompressedNode"
            is_abstract = node_class_name == "AbstractNode"

            # Try to get node count for compressed/abstract nodes
            node_count = None
            if (is_compressed or is_abstract) and hasattr(node, "__len__"):
                try:
                    node_count = len(node)
                except:
                    pass

            # Use existing position if available, otherwise default to (0, 0)
            x, y = 0.0, 0.0
            if hasattr(node, "x") and hasattr(node, "y"):
                x, y = node.x, node.y

            node_state = NodeRenderState(
                node_id=node.name,
                name=node.name,
                x=x,
                y=y,
                is_compressed=is_compressed,
                is_abstract=is_abstract,
                node_count=node_count,
            )
            self._nodes[node.name] = node_state

        # Create render state for each edge (connections)
        edge_id = 0
        for node in graph.nodes:
            for predecessor in node.predecessors:
                edge_state = EdgeRenderState(
                    edge_id=f"edge_{edge_id}",
                    source_node_id=predecessor.name,
                    target_node_id=node.name,
                )
                self._edges[edge_state.edge_id] = edge_state
                edge_id += 1

        # Notify observers
        self.nodes_changed += 1
        self.edges_changed += 1

        print(
            f"[CanvasViewModel] Loaded graph with {len(self._nodes)} nodes and {len(self._edges)} edges"
        )

    def get_nodes(self) -> List[NodeRenderState]:
        """Get all nodes for rendering."""
        return list(self._nodes.values())

    def get_edges(self) -> List[EdgeRenderState]:
        """Get all edges for rendering."""
        return list(self._edges.values())

    def get_node(self, node_id: str) -> Optional[NodeRenderState]:
        """Get a specific node by ID."""
        return self._nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[EdgeRenderState]:
        """Get a specific edge by ID."""
        return self._edges.get(edge_id)

    # Viewport management

    def zoom_in(self, factor: float = 1.2):
        """Zoom in the canvas."""
        self._viewport.zoom_in(factor)
        self.viewport_changed += 1
        print(f"[CanvasViewModel] Zoom in: {self._viewport.zoom_level:.2f}")

    def zoom_out(self, factor: float = 1.2):
        """Zoom out the canvas."""
        self._viewport.zoom_out(factor)
        self.viewport_changed += 1
        print(f"[CanvasViewModel] Zoom out: {self._viewport.zoom_level:.2f}")

    def pan(self, dx: float, dy: float):
        """Pan the canvas."""
        self._viewport.pan(dx, dy)
        self.viewport_changed += 1

    def reset_viewport(self):
        """Reset viewport to default."""
        self._viewport.reset()
        self.viewport_changed += 1
        print("[CanvasViewModel] Viewport reset")

    def get_viewport(self) -> CanvasViewport:
        """Get current viewport state."""
        return self._viewport

    # Node position management (for rendering)

    def update_node_position(self, node_id: str, x: float, y: float):
        """
        Update node position in render state.

        Args:
            node_id: Node identifier
            x: New x coordinate
            y: New y coordinate
        """
        if node_id in self._nodes:
            node = self._nodes[node_id]
            node.x = x
            node.y = y
            self.nodes_changed += 1

    def update_node_positions(self, positions: Dict[str, Tuple[float, float]]):
        """
        Update multiple node positions at once.

        Args:
            positions: Dict mapping node_id to (x, y) tuples
        """
        for node_id, (x, y) in positions.items():
            if node_id in self._nodes:
                node = self._nodes[node_id]
                node.x = x
                node.y = y
        self.nodes_changed += 1

    # Node color management (for visualization)

    def set_node_color(self, node_id: str, color: Optional[str]):
        """
        Set node color for visualization.

        Args:
            node_id: Node identifier
            color: Hex color string (e.g., "#FF0000") or None for default
        """
        if node_id in self._nodes:
            self._nodes[node_id].color = color
            self.nodes_changed += 1

    def clear_node_colors(self):
        """Clear all custom node colors."""
        for node in self._nodes.values():
            node.color = None
        self.nodes_changed += 1

    # Active node tracking (for Forward Processing visualization)

    def set_node_active(self, node_id: str, is_active: bool):
        """
        Set node active state for visualization.

        Args:
            node_id: Node identifier
            is_active: Whether node is currently active
        """
        if node_id in self._nodes:
            self._nodes[node_id].is_active = is_active
            self.nodes_changed += 1

    def clear_active_nodes(self):
        """Clear all active node states."""
        for node in self._nodes.values():
            node.is_active = False
        self.nodes_changed += 1

    # Selection management (Stage 2: Interactive)

    def get_selected_nodes(self) -> List[str]:
        """Get list of selected node IDs."""
        return list(self._selected_nodes)

    def get_selected_edges(self) -> List[str]:
        """Get list of selected edge IDs."""
        return list(self._selected_edges)

    def is_node_selected(self, node_id: str) -> bool:
        """Check if a node is selected."""
        return node_id in self._selected_nodes

    def is_edge_selected(self, edge_id: str) -> bool:
        """Check if an edge is selected."""
        return edge_id in self._selected_edges

    def select_node(self, node_id: str, add_to_selection: bool = False):
        """
        Select a node.

        Args:
            node_id: Node identifier
            add_to_selection: If True, add to existing selection; if False, clear and select
        """
        if not add_to_selection:
            self.clear_selection()

        if node_id in self._nodes:
            self._selected_nodes.add(node_id)
            self._nodes[node_id].is_selected = True
            self.nodes_changed += 1
            print(f"[CanvasViewModel] Node {node_id} selected")

    def deselect_node(self, node_id: str):
        """Deselect a node."""
        if node_id in self._selected_nodes:
            self._selected_nodes.remove(node_id)
            if node_id in self._nodes:
                self._nodes[node_id].is_selected = False
            self.nodes_changed += 1
            print(f"[CanvasViewModel] Node {node_id} deselected")

    def select_edge(self, edge_id: str, add_to_selection: bool = False):
        """
        Select an edge.

        Args:
            edge_id: Edge identifier
            add_to_selection: If True, add to existing selection; if False, clear and select
        """
        if not add_to_selection:
            self.clear_selection()

        if edge_id in self._edges:
            self._selected_edges.add(edge_id)
            self._edges[edge_id].is_selected = True
            self.edges_changed += 1
            print(f"[CanvasViewModel] Edge {edge_id} selected")

    def deselect_edge(self, edge_id: str):
        """Deselect an edge."""
        if edge_id in self._selected_edges:
            self._selected_edges.remove(edge_id)
            if edge_id in self._edges:
                self._edges[edge_id].is_selected = False
            self.edges_changed += 1
            print(f"[CanvasViewModel] Edge {edge_id} deselected")

    def select_nodes_in_rect(
        self, x1: float, y1: float, x2: float, y2: float, add_to_selection: bool = False
    ):
        """
        Select all nodes within a rectangular region.

        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
            add_to_selection: If True, add to existing selection
        """
        if not add_to_selection:
            self.clear_selection()

        # Normalize coordinates
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        selected_count = 0
        for node_id, node in self._nodes.items():
            if min_x <= node.x <= max_x and min_y <= node.y <= max_y:
                self._selected_nodes.add(node_id)
                node.is_selected = True
                selected_count += 1

        if selected_count > 0:
            self.nodes_changed += 1
            print(f"[CanvasViewModel] Selected {selected_count} nodes in rect")

    def clear_selection(self):
        """Clear all selection."""
        if self._selected_nodes or self._selected_edges:
            # Clear node selection
            for node_id in self._selected_nodes:
                if node_id in self._nodes:
                    self._nodes[node_id].is_selected = False
            self._selected_nodes.clear()

            # Clear edge selection
            for edge_id in self._selected_edges:
                if edge_id in self._edges:
                    self._edges[edge_id].is_selected = False
            self._selected_edges.clear()

            self.nodes_changed += 1
            self.edges_changed += 1
            print("[CanvasViewModel] Selection cleared")

    def select_all_nodes(self):
        """Select all nodes."""
        for node_id, node in self._nodes.items():
            self._selected_nodes.add(node_id)
            node.is_selected = True

        if self._nodes:
            self.nodes_changed += 1
            print(f"[CanvasViewModel] Selected all {len(self._nodes)} nodes")

    # Statistics

    def get_node_count(self) -> int:
        """Get number of nodes."""
        return len(self._nodes)

    def get_edge_count(self) -> int:
        """Get number of edges."""
        return len(self._edges)

    def get_bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """
        Get bounding box of all nodes.

        Returns:
            (min_x, min_y, max_x, max_y) or None if no nodes
        """
        if not self._nodes:
            return None

        nodes = self._nodes.values()
        xs = [n.x for n in nodes]
        ys = [n.y for n in nodes]

        return (min(xs), min(ys), max(xs), max(ys))

    # Layout integration

    def apply_layout(
        self, algorithm: str = "sugiyama", direction: str = "LR", **kwargs
    ) -> Optional[Dict[str, Tuple[float, float]]]:
        """Compute and apply layout positions to the loaded graph's nodes.

        This method delegates to `gui_framework.layouts.apply_layout` which will
        try to use the legacy implementations if available and otherwise fall
        back to simple grid/circular/spring layouts.

        Args:
            algorithm: named layout algorithm (e.g., 'sugiyama', 'tree', 'circular', 'grid', 'force')
            direction: 'LR' or 'TB'
            kwargs: forwarded to layout implementation

        Returns:
            Mapping node_id -> (x, y) of applied positions, or None if no graph loaded
        """
        if not self._graph:
            print("[CanvasViewModel] No graph loaded, cannot apply layout")
            return None

        nodes = list(self._graph.nodes)

        def _get_predecessors(node):
            return [p for p in getattr(node, "predecessors", []) if p in nodes]

        from gui_framework.layouts import apply_layout as _apply_layout

        raw_pos = _apply_layout(
            nodes, _get_predecessors, algorithm=algorithm, direction=direction, **kwargs
        )

        if not raw_pos:
            return None

        # Apply positions to canvas nodes by node.name
        self.update_node_positions(raw_pos)
        print(f"[CanvasViewModel] Applied layout '{algorithm}' to {len(raw_pos)} nodes")
        return raw_pos
