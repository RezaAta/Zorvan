"""
PlotConfigViewModel - Pure Python logic for plot configuration dialog.

Manages node selection, filtering, and plot settings without PyQt dependencies.
This ViewModel is completely testable without GUI.
"""

from typing import List, Optional, Set
from dataclasses import dataclass

from ..viewmodels.base import BaseViewModel, ObservableProperty


@dataclass
class NodeInfo:
    """Information about a node available for plotting."""
    name: str
    node_id: str  # For reference
    is_in_subgraph: bool = False
    subgraph_name: Optional[str] = None


class PlotConfigViewModel(BaseViewModel):
    """ViewModel for plot configuration dialog.

    Pure Python logic with no PyQt dependencies. Manages node selection,
    filtering, and max iterations setting for plot configuration.

    Attributes:
        available_nodes: List of all nodes that can be plotted
        selected_nodes: Set of node names selected for plotting
        filter_mode: Current filter ('all', 'mother', or subgraph name)
        max_iterations: Maximum iterations to plot
        filtered_nodes: Nodes visible after applying filter
    """

    # Observable properties
    nodes_changed = ObservableProperty("nodes_changed", default=0)  # Counter
    selection_changed = ObservableProperty("selection_changed", default=0)  # Counter
    filter_changed = ObservableProperty("filter_changed", default=0)  # Counter

    def __init__(self, max_iterations: int = 100):
        """Initialize PlotConfigViewModel.

        Args:
            max_iterations: Default maximum iterations
        """
        super().__init__()

        # Configuration
        self._max_iterations = max_iterations

        # Node management
        self._available_nodes: List[NodeInfo] = []
        self._selected_nodes: Set[str] = set()  # Node names
        self._filter_mode: str = 'all'  # 'all', 'mother', or subgraph name
        self._filtered_nodes: List[NodeInfo] = []

        # Subgraph tracking
        self._subgraph_names: List[str] = []

    def initialize(self):
        """Called when View is shown."""
        print("[PlotConfigViewModel] Configuration dialog initialized")

    def cleanup(self):
        """Called when View is closed."""
        print("[PlotConfigViewModel] Configuration dialog cleanup")

    # Node management

    def load_nodes(self, nodes: List[NodeInfo]):
        """Load available nodes for selection.

        Args:
            nodes: List of NodeInfo objects
        """
        self._available_nodes = list(nodes)
        
        # Extract unique subgraph names
        self._subgraph_names = sorted(list(set(
            node.subgraph_name 
            for node in nodes 
            if node.subgraph_name is not None
        )))

        # Apply current filter
        self._apply_filter()
        self.nodes_changed += 1
        print(f"[PlotConfigViewModel] Loaded {len(nodes)} nodes")

    def get_available_nodes(self) -> List[NodeInfo]:
        """Get all available nodes."""
        return list(self._available_nodes)

    def get_filtered_nodes(self) -> List[NodeInfo]:
        """Get nodes after applying current filter."""
        return list(self._filtered_nodes)

    def get_subgraph_names(self) -> List[str]:
        """Get list of subgraph names."""
        return list(self._subgraph_names)

    # Selection management

    def select_node(self, node_name: str):
        """Select a node for plotting.

        Args:
            node_name: Name of the node to select
        """
        if node_name not in self._selected_nodes:
            self._selected_nodes.add(node_name)
            self.selection_changed += 1
            print(f"[PlotConfigViewModel] Selected node '{node_name}'")

    def deselect_node(self, node_name: str):
        """Deselect a node.

        Args:
            node_name: Name of the node to deselect
        """
        if node_name in self._selected_nodes:
            self._selected_nodes.remove(node_name)
            self.selection_changed += 1
            print(f"[PlotConfigViewModel] Deselected node '{node_name}'")

    def toggle_node(self, node_name: str):
        """Toggle node selection state.

        Args:
            node_name: Name of the node to toggle
        """
        if node_name in self._selected_nodes:
            self.deselect_node(node_name)
        else:
            self.select_node(node_name)

    def is_node_selected(self, node_name: str) -> bool:
        """Check if a node is selected.

        Args:
            node_name: Node name to check

        Returns:
            True if node is selected
        """
        return node_name in self._selected_nodes

    def get_selected_nodes(self) -> List[str]:
        """Get list of selected node names."""
        return sorted(list(self._selected_nodes))

    def select_all_visible(self):
        """Select all currently visible (filtered) nodes."""
        for node in self._filtered_nodes:
            self._selected_nodes.add(node.name)
        
        if self._filtered_nodes:
            self.selection_changed += 1
            print(f"[PlotConfigViewModel] Selected all {len(self._filtered_nodes)} visible nodes")

    def deselect_all(self):
        """Deselect all nodes."""
        if self._selected_nodes:
            self._selected_nodes.clear()
            self.selection_changed += 1
            print("[PlotConfigViewModel] Deselected all nodes")

    def get_selection_count(self) -> int:
        """Get number of selected nodes."""
        return len(self._selected_nodes)

    # Filter management

    def set_filter(self, filter_mode: str):
        """Set the filter mode.

        Args:
            filter_mode: Filter to apply ('all', 'mother', or subgraph name)
        """
        if filter_mode != self._filter_mode:
            self._filter_mode = filter_mode
            self._apply_filter()
            self.filter_changed += 1
            print(f"[PlotConfigViewModel] Filter set to '{filter_mode}'")

    def get_filter(self) -> str:
        """Get current filter mode."""
        return self._filter_mode

    def _apply_filter(self):
        """Apply the current filter to nodes."""
        if self._filter_mode == 'all':
            # Show all nodes
            self._filtered_nodes = list(self._available_nodes)
        elif self._filter_mode == 'mother':
            # Show only nodes not in any subgraph
            self._filtered_nodes = [
                node for node in self._available_nodes
                if not node.is_in_subgraph
            ]
        else:
            # Show nodes from specific subgraph
            self._filtered_nodes = [
                node for node in self._available_nodes
                if node.subgraph_name == self._filter_mode
            ]

    # Max iterations

    def set_max_iterations(self, max_iterations: int):
        """Set maximum iterations.

        Args:
            max_iterations: Maximum iterations (minimum 10)
        """
        self._max_iterations = max(10, max_iterations)
        print(f"[PlotConfigViewModel] Max iterations set to {self._max_iterations}")

    def get_max_iterations(self) -> int:
        """Get maximum iterations setting."""
        return self._max_iterations

    # Validation

    def has_selection(self) -> bool:
        """Check if any nodes are selected."""
        return len(self._selected_nodes) > 0

    def get_filter_options(self) -> List[str]:
        """Get available filter options.

        Returns:
            List of filter options: ['all', 'mother', subgraph1, subgraph2, ...]
        """
        options = ['all', 'mother']
        options.extend(self._subgraph_names)
        return options
