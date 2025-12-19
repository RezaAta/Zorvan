"""Real-time plotting window for computational graph nodes."""

import matplotlib
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

matplotlib.use("QtAgg")
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

try:
    import mplcursors
except Exception:
    mplcursors = None
try:
    from .plot_window_pyqtgraph import PlotWindowPG
except Exception:
    PlotWindowPG = None


class PlotConfigDialog(QDialog):
    """Dialog for configuring which nodes to plot."""

    def __init__(self, graph, default_max_iter=100, parent=None):
        super().__init__(parent)
        self.graph = graph
        self.setWindowTitle("Configure Plot")
        self.setModal(False)  # Non-blocking dialog
        self.resize(400, 500)

        layout = QVBoxLayout()

        # === Phase 2: Graph/Subgraph Filter ===
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by:"))
        self.graph_filter_combo = QComboBox()
        self.graph_filter_combo.addItem("All Nodes")
        self.graph_filter_combo.addItem("Mother Graph Only")

        # Add subgraphs
        sub_graphs = getattr(graph, "sub_graphs", [])
        for sg in sub_graphs:
            sg_name = getattr(sg, "graph_name", "SubGraph")
            self.graph_filter_combo.addItem(f"SubGraph: {sg_name}")

        self.graph_filter_combo.currentIndexChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.graph_filter_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Instructions
        instructions = QLabel("Select nodes to plot:")
        layout.addWidget(instructions)

        # Node list with checkboxes
        self.node_list = QListWidget()
        # Use NoSelection to prevent selection highlighting that causes cramping
        self.node_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        # Set spacing between items to prevent cramping
        self.node_list.setSpacing(2)

        # Store all nodes for filtering
        self._all_nodes = sorted(graph.nodes, key=lambda n: n.name)
        self._sub_graphs = sub_graphs

        # Add all nodes as checkable items
        self._populate_node_list(self._all_nodes)

        layout.addWidget(self.node_list)

        # Max iterations
        iter_layout = QHBoxLayout()
        iter_layout.addWidget(QLabel("Max iterations:"))
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setMinimum(10)
        self.max_iter_spin.setMaximum(100000)
        self.max_iter_spin.setValue(default_max_iter)  # Use provided default
        self.max_iter_spin.setSingleStep(10)
        iter_layout.addWidget(self.max_iter_spin)
        iter_layout.addStretch()
        layout.addLayout(iter_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _populate_node_list(self, nodes):
        """Populate the node list with given nodes."""
        # Remember checked states
        checked_nodes = set()
        for i in range(self.node_list.count()):
            item = self.node_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                node = item.data(Qt.ItemDataRole.UserRole)
                checked_nodes.add(node)

        self.node_list.clear()

        for node in sorted(nodes, key=lambda n: n.name):
            item = QListWidgetItem(node.name)
            item.setData(Qt.ItemDataRole.UserRole, node)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            # Restore check state if node was previously checked
            if node in checked_nodes:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.node_list.addItem(item)

    def _apply_filter(self, index):
        """Apply the graph/subgraph filter."""
        if index == 0:
            # "All Nodes"
            self._populate_node_list(self._all_nodes)
        elif index == 1:
            # "Mother Graph Only" - nodes not in any subgraph
            nodes_in_subgraphs = set()
            for sg in self._sub_graphs:
                for node in getattr(sg, "nodes", []):
                    nodes_in_subgraphs.add(node)
            mother_only = [n for n in self._all_nodes if n not in nodes_in_subgraphs]
            self._populate_node_list(mother_only if mother_only else self._all_nodes)
        else:
            # Subgraph filter (index - 2 because of "All Nodes" and "Mother Graph Only")
            sg_index = index - 2
            if 0 <= sg_index < len(self._sub_graphs):
                sg = self._sub_graphs[sg_index]
                sg_nodes = getattr(sg, "nodes", [])
                self._populate_node_list(sg_nodes)

    def get_selected_nodes(self):
        """Get list of selected nodes."""
        selected = []
        for i in range(self.node_list.count()):
            item = self.node_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                node = item.data(Qt.ItemDataRole.UserRole)
                selected.append(node)
        return selected

    def get_max_iterations(self):
        """Get max iterations value."""
        return self.max_iter_spin.value()


class PlotWindow(QWidget):
    """Window for real-time plotting of node values."""

    def __init__(self, nodes, max_iterations, parent=None):
        super().__init__(parent)
        self.nodes = list(nodes)  # Keep as list to maintain order
        self.backend = "matplotlib"
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.parent_window = parent

        # Data storage: {node: [values]}
        self.data = {node: [] for node in nodes}
        self.iterations = []

        # Phase 3: Active subgraph tracking for plot optimization
        self._active_subgraph = None  # Currently processing subgraph
        self._track_active_only = False  # When True, skip nodes not in active subgraph

        # Colors for different nodes
        self.colors = [
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

        self.setup_ui()
        self.setup_plot()

    def setup_ui(self):
        """Setup the UI layout."""
        self.setWindowTitle("Node Values Plot")
        self.resize(900, 600)

        layout = QVBoxLayout()

        # Matplotlib canvas - give it maximum space
        self.figure = Figure(figsize=(8, 5), facecolor="white")
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(
            self.canvas, stretch=1
        )  # Stretch factor of 1 = takes all available space

        # Controls - compact layout at the bottom
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins
        control_layout.setSpacing(8)  # Compact spacing

        self.clear_btn = QPushButton("Clear")
        try:
            self.clear_btn.setProperty("themed", True)
            self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.clear_btn.setMouseTracking(True)
        except Exception:
            pass
        self.clear_btn.clicked.connect(self.clear_plot)
        self.clear_btn.setMaximumWidth(80)
        control_layout.addWidget(self.clear_btn)

        self.remove_btn = QPushButton("Remove Selected")
        try:
            self.remove_btn.setProperty("themed", True)
            self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.remove_btn.setMouseTracking(True)
        except Exception:
            pass
        self.remove_btn.clicked.connect(self.remove_selected_node)
        self.remove_btn.setMaximumWidth(130)
        control_layout.addWidget(self.remove_btn)

        self.close_btn = QPushButton("Close")
        try:
            self.close_btn.setProperty("themed", True)
            self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.close_btn.setMouseTracking(True)
        except Exception:
            pass
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setMaximumWidth(80)
        control_layout.addWidget(self.close_btn)

        self.autoscale_check = QCheckBox("Auto-scale Y")
        self.autoscale_check.setChecked(True)
        control_layout.addWidget(self.autoscale_check)

        # Phase 3: Track only active subgraph checkbox
        self.track_active_check = QCheckBox("Track active subgraph only")
        self.track_active_check.setToolTip(
            "When enabled, only update values for nodes in the currently "
            "processing subgraph (prevents flat lines during queue runs)"
        )
        self.track_active_check.stateChanged.connect(self._on_track_active_changed)
        control_layout.addWidget(self.track_active_check)

        control_layout.addStretch()

        # Node list dropdown for removal
        self.node_combo = QComboBox()
        self.node_combo.setMaximumWidth(150)
        self.update_node_combo()
        control_layout.addWidget(QLabel("Remove:"))
        control_layout.addWidget(self.node_combo)

        self.iteration_label = QLabel("Iteration: 0 / {}".format(self.max_iterations))
        self.iteration_label.setMinimumWidth(150)
        control_layout.addWidget(self.iteration_label)

        layout.addLayout(
            control_layout, stretch=0
        )  # Stretch factor of 0 = use minimum space needed

        self.setLayout(layout)

    def _generate_unique_legend_label(self, base_label, existing_labels):
        """Return a unique label based on base_label, appending ' (N)' when needed.

        Modifies the provided existing_labels list in-place by appending the returned
        unique label so subsequent calls are aware of already-used labels.
        """
        try:
            if base_label not in existing_labels:
                existing_labels.append(base_label)
                return base_label
            suffix = 1
            while True:
                candidate = f"{base_label} ({suffix})"
                if candidate not in existing_labels:
                    existing_labels.append(candidate)
                    return candidate
                suffix += 1
        except Exception:
            # Fallback to base label on unexpected error
            return base_label

    def update_node_combo(self):
        """Update the combo box with current nodes."""
        self.node_combo.clear()
        for node in self.nodes:
            self.node_combo.addItem(node.name, node)

    def remove_selected_node(self):
        """Remove the selected node from the plot."""
        if self.node_combo.count() == 0:
            return

        node = self.node_combo.currentData()
        if node in self.nodes:
            self.nodes.remove(node)

            # Remove line from plot
            if node in self.lines:
                self.lines[node].remove()
                del self.lines[node]

            # Remove data
            if node in self.data:
                del self.data[node]

            # Update combo box
            self.update_node_combo()

            # Rebuild legend with unique labels to avoid duplicate entries
            if self.nodes:
                # Remove existing legend if present
                legend = self.ax.get_legend()
                if legend:
                    legend.remove()
                existing_labels = []
                # Reassign labels for lines to ensure uniqueness before creating legend
                for n in self.nodes:
                    if n in self.lines:
                        unique_label = self._generate_unique_legend_label(
                            n.name, existing_labels
                        )
                        try:
                            self.lines[n].set_label(unique_label)
                        except Exception:
                            pass
                # Recreate legend
                self.ax.legend(loc="upper right")
            else:
                # Remove legend if no nodes left
                legend = self.ax.get_legend()
                if legend:
                    legend.remove()
            self.canvas.draw()

    def add_node(self, node):
        """Add a new node to the plot."""
        if node in self.nodes:
            return  # Already plotting this node

        self.nodes.append(node)
        self.data[node] = []

        # Add line for this node
        color = self.colors[len(self.nodes) % len(self.colors)]
        # Ensure legend labels are unique (avoid duplicate legend entries)
        try:
            existing_labels = [l.get_label() for l in self.lines.values()]
        except Exception:
            existing_labels = []
        unique_label = self._generate_unique_legend_label(node.name, existing_labels)
        (line,) = self.ax.plot([], [], label=unique_label, color=color, linewidth=2)
        self.lines[node] = line

        # Update combo box
        self.update_node_combo()

        # Redraw
        self.ax.legend(loc="upper right")
        self.canvas.draw()

    def setup_plot(self):
        """Setup the matplotlib plot."""
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("white")
        self.ax.set_xlabel("Iteration")
        self.ax.set_ylabel("Value")
        self.ax.set_title("Node Values Over Time")
        self.ax.grid(True, alpha=0.3)

        # Set initial x-axis limits
        self.ax.set_xlim(0, self.max_iterations)

        # Create line objects for each node
        self.lines = {}
        # Ensure labels are unique when first creating lines
        existing_labels = []
        for i, node in enumerate(self.nodes):
            color = self.colors[i % len(self.colors)]
            unique_label = self._generate_unique_legend_label(
                node.name, existing_labels
            )
            (line,) = self.ax.plot(
                [], [], label=unique_label, color=color, linewidth=2, antialiased=True
            )
            self.lines[node] = line

        # Only show legend if there are nodes
        if self.nodes:
            self.ax.legend(loc="upper right")
            # Setup mplcursors hover if available
            if mplcursors is not None:
                try:
                    cursor = mplcursors.cursor(list(self.lines.values()), hover=True)

                    def on_add(sel):
                        artist = sel.artist
                        node_name = None
                        for n, l in self.lines.items():
                            if l == artist:
                                node_name = n.name
                                break
                        if node_name is not None:
                            x, y = sel.target
                            sel.annotation.set_text(f"{node_name}: {y:.4f}")

                    cursor.connect("add", on_add)
                except Exception:
                    pass
        self.canvas.draw()

    def update_plot(self, iteration, active_subgraph=None):
        """Update plot with current node values.

        Args:
            iteration: Current iteration number
            active_subgraph: Optional Graph object representing the currently
                           processing subgraph. Used for optimization.
        """
        self.current_iteration = iteration
        self.iteration_label.setText(
            "Iteration: {} / {}".format(iteration, self.max_iterations)
        )

        # Update active subgraph reference
        if active_subgraph is not None:
            self._active_subgraph = active_subgraph

        # Determine which nodes to update based on tracking mode
        if self._track_active_only and self._active_subgraph is not None:
            # Get nodes in the active subgraph
            active_nodes = set(getattr(self._active_subgraph, "nodes", []))
            nodes_to_update = [n for n in self.nodes if n in active_nodes]
        else:
            nodes_to_update = self.nodes

        # Collect current values
        self.iterations.append(iteration)
        for node in self.nodes:
            # Skip nodes not in active subgraph when tracking is enabled
            if node not in nodes_to_update:
                # Append the previous value (or 0) to keep arrays aligned
                if self.data[node]:
                    self.data[node].append(self.data[node][-1])
                else:
                    self.data[node].append(0)
                continue

            value = node.value
            # Handle list/array values (take first element or compute mean)
            if isinstance(value, (list, tuple)):
                if len(value) > 0:
                    if isinstance(value[0], (int, float)):
                        value = np.mean(value)  # Average for numeric lists
                    else:
                        value = len(value)  # Count for non-numeric
                else:
                    value = 0
            elif value is None:
                value = 0

            self.data[node].append(float(value))

        # Update line data
        for node in self.nodes:
            self.lines[node].set_data(self.iterations, self.data[node])

        # Auto-scale Y axis if enabled
        if self.autoscale_check.isChecked():
            # Get all values to determine Y limits
            all_values = []
            for values in self.data.values():
                all_values.extend(values)

            if all_values:
                y_min = min(all_values)
                y_max = max(all_values)
                # Add 10% padding
                y_range = y_max - y_min
                if y_range == 0:
                    y_range = 1
                self.ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)

        # Adjust X axis if we exceed max iterations
        if iteration > self.max_iterations:
            self.ax.set_xlim(0, iteration + 10)

        self.canvas.draw()

    def clear_plot(self):
        """Clear all plot data."""
        self.current_iteration = 0
        self.iterations = []
        for node in self.nodes:
            self.data[node] = []
            self.lines[node].set_data([], [])

        self.ax.set_xlim(0, self.max_iterations)
        self.iteration_label.setText("Iteration: 0 / {}".format(self.max_iterations))
        self.canvas.draw()

    # === Phase 3: Active subgraph tracking ===

    def _on_track_active_changed(self, state):
        """Handle track active subgraph checkbox state change."""
        self._track_active_only = state == 2  # Qt.CheckState.Checked

    def set_active_subgraph(self, subgraph):
        """Set the currently active subgraph for tracking.

        Args:
            subgraph: Graph object representing the active subgraph,
                     or None for the mother graph
        """
        self._active_subgraph = subgraph

    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up matplotlib resources
        self.figure.clear()
        event.accept()


def create_plot_window(nodes, max_iterations, parent=None, backend="auto"):
    """Factory to create a PlotWindow using the selected backend.

    backend: 'matplotlib', 'pyqtgraph', or 'auto'.
      - 'auto': use PyQtGraph if installed, otherwise Matplotlib
    """
    backend_choice = backend
    if backend_choice == "auto":
        backend_choice = "pyqtgraph" if PlotWindowPG is not None else "matplotlib"

    if backend_choice == "pyqtgraph":
        if PlotWindowPG is None:
            # Fallback to Matplotlib implementation
            return PlotWindow(nodes, max_iterations, parent)
        else:
            return PlotWindowPG(nodes, max_iterations, parent)
    else:
        # default to Matplotlib implementation
        return PlotWindow(nodes, max_iterations, parent)
