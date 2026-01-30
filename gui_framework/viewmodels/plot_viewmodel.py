"""
PlotViewModel - Pure Python logic for plot window management.

Manages plot data, node selection, and backend configuration using StateStore.
This ViewModel is completely testable without PyQt dependencies.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..events.bus import Event, EventType
from ..viewmodels.base import BaseViewModel, ObservableProperty


@dataclass
class PlotDataPoint:
    """Single data point for plotting."""

    iteration: int
    value: float


class PlotViewModel(BaseViewModel):
    """ViewModel for plot window management.

    Pure Python logic with no PyQt dependencies. Manages plot data collection,
    node selection, backend selection, and provides methods for plot updates.

    Attributes:
        plotted_nodes: List of node names being plotted
        plot_data: Dictionary mapping node name to list of data points
        buffer_size: Maximum number of data points to store per node
        current_iteration: Current execution iteration
        backend: Selected backend ('matplotlib' or 'pyqtgraph')
    """

    # Observable properties
    data_updated = ObservableProperty("data_updated", default=0)  # Counter
    nodes_changed = ObservableProperty("nodes_changed", default=0)  # Counter
    backend_changed = ObservableProperty("backend_changed", default=0)  # Counter

    # Available backends
    BACKENDS = ["matplotlib", "pyqtgraph"]

    def __init__(self, buffer_size: int = 10000, backend: str = "matplotlib"):
        """Initialize PlotViewModel.

        Args:
            buffer_size: Maximum data points to store per node (default: 10000)
            backend: Initial backend ('matplotlib' or 'pyqtgraph')
        """
        super().__init__()

        # Plot configuration
        self._buffer_size = buffer_size
        self._backend = backend if backend in self.BACKENDS else "matplotlib"

        # Plot data storage
        self._plotted_nodes: List[str] = []  # Node names to plot
        self._plot_data: Dict[str, List[PlotDataPoint]] = (
            {}
        )  # node_name -> [data points]
        self._current_iteration = 0

        # Color management
        self._colors = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        ]
        self._node_colors: Dict[str, str] = {}  # node_name -> color

    def initialize(self):
        """Called when View is shown."""
        print("[PlotViewModel] Plot window initialized")

    def cleanup(self):
        """Called when View is closed."""
        print("[PlotViewModel] Plot window cleanup")

    # Configuration methods

    def set_buffer_size(self, buffer_size: int):
        """Set maximum data points to store per node.

        Args:
            buffer_size: Maximum data points (minimum 100)
        """
        self._buffer_size = max(100, buffer_size)
        print(f"[PlotViewModel] Buffer size set to {self._buffer_size}")

    def get_buffer_size(self) -> int:
        """Get buffer size setting."""
        return self._buffer_size

    def set_backend(self, backend: str):
        """Set plot backend.

        Args:
            backend: Backend name ('matplotlib' or 'pyqtgraph')
        """
        if backend in self.BACKENDS and backend != self._backend:
            self._backend = backend
            self.backend_changed += 1
            print(f"[PlotViewModel] Backend changed to {backend}")

            # Publish event
            self._event_bus.publish(
                Event(
                    type=EventType.THEME_UPDATED,  # Reusing for config changes
                    payload={"plot_backend": backend},
                )
            )

    def get_backend(self) -> str:
        """Get current backend."""
        return self._backend

    # Node management

    def add_node(self, node_name: str):
        """Add a node to the plot.

        Args:
            node_name: Name of the node to plot
        """
        if node_name not in self._plotted_nodes:
            self._plotted_nodes.append(node_name)
            self._plot_data[node_name] = []

            # Assign color
            if node_name not in self._node_colors:
                color_index = len(self._node_colors) % len(self._colors)
                self._node_colors[node_name] = self._colors[color_index]

            self.nodes_changed += 1
            print(f"[PlotViewModel] Added node '{node_name}' to plot")

    def remove_node(self, node_name: str):
        """Remove a node from the plot.

        Args:
            node_name: Name of the node to remove
        """
        if node_name in self._plotted_nodes:
            self._plotted_nodes.remove(node_name)
            if node_name in self._plot_data:
                del self._plot_data[node_name]
            if node_name in self._node_colors:
                del self._node_colors[node_name]

            self.nodes_changed += 1
            print(f"[PlotViewModel] Removed node '{node_name}' from plot")

    def set_nodes(self, node_names: List[str]):
        """Set the list of nodes to plot (replaces existing).

        Args:
            node_names: List of node names to plot
        """
        self._plotted_nodes = list(node_names)

        # Clear old data and create new
        self._plot_data = {name: [] for name in node_names}

        # Assign colors
        self._node_colors = {}
        for i, name in enumerate(node_names):
            self._node_colors[name] = self._colors[i % len(self._colors)]

        self.nodes_changed += 1
        print(f"[PlotViewModel] Set {len(node_names)} nodes to plot")

    def get_plotted_nodes(self) -> List[str]:
        """Get list of nodes being plotted."""
        return list(self._plotted_nodes)

    def get_node_color(self, node_name: str) -> Optional[str]:
        """Get color for a node.

        Args:
            node_name: Node name

        Returns:
            Hex color string or None
        """
        return self._node_colors.get(node_name)

    # Data management

    def add_data_point(
        self, node_name: str, value: float, iteration: Optional[int] = None
    ):
        """Add a data point for a node.

        Args:
            node_name: Name of the node
            value: Value to plot
            iteration: Iteration number (uses current_iteration if None)
        """
        if node_name not in self._plotted_nodes:
            return

        iter_num = iteration if iteration is not None else self._current_iteration

        # Add data point
        data_point = PlotDataPoint(iteration=iter_num, value=value)
        self._plot_data[node_name].append(data_point)

        # Trim data if exceeds buffer size
        if len(self._plot_data[node_name]) > self._buffer_size:
            self._plot_data[node_name] = self._plot_data[node_name][
                -self._buffer_size :
            ]

        self.data_updated += 1

    def add_data_points(self, data: Dict[str, float], iteration: Optional[int] = None):
        """Add multiple data points at once.

        Args:
            data: Dictionary mapping node name to value
            iteration: Iteration number (uses current_iteration if None)
        """
        iter_num = iteration if iteration is not None else self._current_iteration

        for node_name, value in data.items():
            if node_name in self._plotted_nodes:
                data_point = PlotDataPoint(iteration=iter_num, value=value)
                self._plot_data[node_name].append(data_point)

                # Trim data if exceeds buffer size
                if len(self._plot_data[node_name]) > self._buffer_size:
                    self._plot_data[node_name] = self._plot_data[node_name][
                        -self._buffer_size :
                    ]

        if data:
            self.data_updated += 1

    def get_plot_data(self, node_name: str) -> List[PlotDataPoint]:
        """Get plot data for a node.

        Args:
            node_name: Name of the node

        Returns:
            List of data points
        """
        return list(self._plot_data.get(node_name, []))

    def get_all_plot_data(self) -> Dict[str, List[PlotDataPoint]]:
        """Get all plot data.

        Returns:
            Dictionary mapping node name to data points
        """
        return {name: list(points) for name, points in self._plot_data.items()}

    def clear_data(self):
        """Clear all plot data."""
        for node_name in self._plot_data:
            self._plot_data[node_name] = []

        self._current_iteration = 0
        self.data_updated += 1
        print("[PlotViewModel] Plot data cleared")

    # Iteration tracking

    def set_current_iteration(self, iteration: int):
        """Set current execution iteration.

        Args:
            iteration: Current iteration number
        """
        self._current_iteration = iteration

    def get_current_iteration(self) -> int:
        """Get current execution iteration."""
        return self._current_iteration

    # Statistics

    def get_data_point_count(self, node_name: str) -> int:
        """Get number of data points for a node.

        Args:
            node_name: Node name

        Returns:
            Number of data points
        """
        return len(self._plot_data.get(node_name, []))

    def get_value_range(self, node_name: str) -> Optional[Tuple[float, float]]:
        """Get min and max values for a node.

        Args:
            node_name: Node name

        Returns:
            (min_value, max_value) or None if no data
        """
        data = self._plot_data.get(node_name, [])
        if not data:
            return None

        values = [point.value for point in data]
        return (min(values), max(values))

    def get_iteration_range(self) -> Tuple[int, int]:
        """Get min and max iteration numbers across all data.

        Returns:
            (min_iteration, max_iteration)
        """
        all_iterations = []
        for data_points in self._plot_data.values():
            all_iterations.extend([point.iteration for point in data_points])

        if not all_iterations:
            return (0, 0)

        return (min(all_iterations), max(all_iterations))
