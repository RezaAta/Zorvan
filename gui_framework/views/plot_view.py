"""
PlotView: PyQt6 UI for displaying real-time plots.

This view provides the user interface for displaying node value plots,
supporting both Matplotlib and PyQtGraph backends with automatic backend switching.
"""

try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

    class QWidget:
        def __init__(self, parent=None):
            pass


from ..viewmodels.base import BaseViewModel

# Import plotting backends
MATPLOTLIB_AVAILABLE = False
PYQTGRAPH_AVAILABLE = False

try:
    import matplotlib

    matplotlib.use("QtAgg")
    import numpy as np
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    pass

try:
    import pyqtgraph as pg

    pg.setConfigOptions(antialias=True)
    try:
        pg.setConfigOptions(useOpenGL=True, useQOpenGLWidget=True)
    except Exception:
        try:
            pg.setConfigOptions(useOpenGL=True)
        except Exception:
            pass
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    pass


if PYQT_AVAILABLE:
    from .base import BaseView

    class PlotView(BaseView):
        """
        PyQt6 view for real-time node value plotting.

        Features:
        - Dual backend support (Matplotlib/PyQtGraph)
        - Real-time data updates
        - Node selection/removal
        - Clear plot functionality
        - Dynamic legend
        - Auto-scaling

        Example:
            >>> from gui_framework.viewmodels.plot_viewmodel import PlotViewModel
            >>> vm = PlotViewModel(max_iterations=1000, backend='matplotlib')
            >>> vm.set_nodes(['A', 'B', 'C'])
            >>> view = PlotView(vm, parent=main_window)
            >>> view.show()
        """

        def __init__(self, viewmodel: BaseViewModel, parent: QWidget = None):
            """
            Initialize PlotView.

            Args:
                viewmodel: PlotViewModel instance
                parent: Parent Qt widget (pass None for standalone window)
            """
            # Pass None as parent to make this a standalone top-level window
            super().__init__(viewmodel, None)
            # Backwards compatibility: expose 'viewmodel' attribute
            self.viewmodel = viewmodel
            self._parent_window = parent  # Keep reference for window positioning
            self.setWindowTitle("Zorvan - Node Values Plot")
            self.resize(900, 600)

            # Plot components
            self.plot_widget = None
            self.matplotlib_canvas = None
            self.matplotlib_axes = None
            self.pyqtgraph_plot = None
            self._line_items = {}  # node_name -> plot item

            # State for legacy features
            self._paused = False
            self._autoscale_y = True
            self._track_active_only = False
            self._active_subgraph = None

            self._setup_ui()
            # Connect signals after UI is setup
            self._connect_signals()
            self._initialize_backend()

        def _initialize_backend(self):
            """Initialize the view backend from the viewmodel."""
            backend = self.get_viewmodel().get_backend()
            self._switch_backend(backend)

        def _connect_signals(self):
            """Connect ViewModel signals to View updates."""
            vm = self.get_viewmodel()
            # Observe counters via BaseViewModel.observe_property
            vm.observe_property(
                "data_updated", lambda old, new: self._on_data_updated(new)
            )
            vm.observe_property(
                "nodes_changed", lambda old, new: self._on_nodes_changed(new)
            )
            vm.observe_property(
                "backend_changed", lambda old, new: self._on_backend_updated(new)
            )

        def _setup_ui(self):
            """Create and layout the UI widgets."""
            layout = QVBoxLayout(self)

            # Backend selector (top)
            backend_layout = QHBoxLayout()
            backend_layout.addWidget(QLabel("Backend:"))

            self.backend_combo = QComboBox()
            if MATPLOTLIB_AVAILABLE:
                self.backend_combo.addItem("Matplotlib", "matplotlib")
            if PYQTGRAPH_AVAILABLE:
                self.backend_combo.addItem("PyQtGraph", "pyqtgraph")

            # Set current backend
            current_backend = self.viewmodel.get_backend()
            for i in range(self.backend_combo.count()):
                if self.backend_combo.itemData(i) == current_backend:
                    self.backend_combo.setCurrentIndex(i)
                    break

            self.backend_combo.currentIndexChanged.connect(self._on_backend_changed)
            backend_layout.addWidget(self.backend_combo)

            # Buffer size control
            backend_layout.addSpacing(20)
            backend_layout.addWidget(QLabel("Buffer Size:"))
            self.buffer_size_spin = QSpinBox()
            self.buffer_size_spin.setRange(100, 10000000)
            self.buffer_size_spin.setSingleStep(1000)
            self.buffer_size_spin.setValue(self.viewmodel.get_buffer_size())
            self.buffer_size_spin.setToolTip("Maximum data points to store per node")
            self.buffer_size_spin.valueChanged.connect(self._on_buffer_size_changed)
            backend_layout.addWidget(self.buffer_size_spin)

            backend_layout.addStretch()

            # Iteration label
            self.iteration_label = QLabel("Iteration: 0")
            self.iteration_label.setMinimumWidth(150)
            backend_layout.addWidget(self.iteration_label)

            layout.addLayout(backend_layout)

            # Plot container (dynamically populated based on backend)
            self.plot_container_layout = QVBoxLayout()
            layout.addLayout(self.plot_container_layout)

            # Controls row 1 (main actions)
            controls_layout = QHBoxLayout()

            self.clear_button = QPushButton("Clear")
            self.clear_button.clicked.connect(self._on_clear_clicked)
            controls_layout.addWidget(self.clear_button)

            self.reset_zoom_button = QPushButton("Reset Zoom")
            self.reset_zoom_button.clicked.connect(self._on_reset_zoom_clicked)
            controls_layout.addWidget(self.reset_zoom_button)

            controls_layout.addStretch()

            # Checkboxes for plot options
            self.autoscale_check = QCheckBox("Auto-scale Y")
            self.autoscale_check.setChecked(True)
            self.autoscale_check.stateChanged.connect(self._on_autoscale_changed)
            controls_layout.addWidget(self.autoscale_check)

            self.pause_check = QCheckBox("Pause Plot")
            self.pause_check.setChecked(False)
            self.pause_check.stateChanged.connect(self._on_pause_changed)
            controls_layout.addWidget(self.pause_check)

            self.antialias_check = QCheckBox("Antialiasing")
            self.antialias_check.setChecked(True)
            self.antialias_check.setToolTip(
                "Disable for better performance with noisy data"
            )
            self.antialias_check.stateChanged.connect(self._on_antialias_changed)
            controls_layout.addWidget(self.antialias_check)

            self.track_active_check = QCheckBox("Track active subgraph")
            self.track_active_check.setToolTip(
                "Only update nodes in the currently processing subgraph"
            )
            self.track_active_check.stateChanged.connect(self._on_track_active_changed)
            controls_layout.addWidget(self.track_active_check)

            layout.addLayout(controls_layout)

            # Controls row 2 (node management)
            node_controls = QHBoxLayout()

            node_controls.addWidget(QLabel("Plotted Nodes:"))
            self.node_list_widget = QListWidget()
            self.node_list_widget.setMaximumHeight(100)
            self.node_list_widget.setSelectionMode(
                QListWidget.SelectionMode.SingleSelection
            )
            node_controls.addWidget(self.node_list_widget)

            self.remove_node_button = QPushButton("Remove Selected")
            self.remove_node_button.clicked.connect(self._on_remove_node_clicked)
            node_controls.addWidget(self.remove_node_button)

            layout.addLayout(node_controls)

            # Status label
            self.status_label = QLabel("Ready")
            layout.addWidget(self.status_label)

        def _bind_viewmodel(self):
            """Bind view to PlotViewModel observables and initialize UI state."""
            try:
                # Ensure node list and plot reflect current ViewModel
                self._update_node_list()
                # Set backend combo to current backend
                backend = self.get_viewmodel().get_backend()
                for i in range(self.backend_combo.count()):
                    if self.backend_combo.itemData(i) == backend:
                        self.backend_combo.setCurrentIndex(i)
                        break
                # Initialize plot content
                self._refresh_plot()
            except Exception:
                pass

        def _create_pyqtgraph_backend(self):
            """Create PyQtGraph backend."""
            self.pyqtgraph_plot = pg.PlotWidget()

            try:
                self.pyqtgraph_plot.setBackground("w")
            except Exception:
                try:
                    self.pyqtgraph_plot.setBackground((255, 255, 255))
                except Exception:
                    pass

            self.pyqtgraph_plot.showGrid(x=True, y=True, alpha=0.3)
            self.pyqtgraph_plot.setLabel("bottom", "Iteration")
            self.pyqtgraph_plot.setLabel("left", "Value")
            self.pyqtgraph_plot.setTitle("Node Values Over Time")

            self.plot_widget = self.pyqtgraph_plot
            self.plot_container_layout.addWidget(self.plot_widget)

            self.status_label.setText("PyQtGraph backend active")

        def _create_matplotlib_backend(self):
            """Create Matplotlib backend."""
            # Create Figure and Canvas
            self.matplotlib_canvas = FigureCanvas(Figure(figsize=(5, 4)))
            self.matplotlib_axes = self.matplotlib_canvas.figure.add_subplot(111)

            self.plot_widget = self.matplotlib_canvas
            self.plot_container_layout.addWidget(self.plot_widget)

            # Configure axes
            self.matplotlib_axes.set_xlabel("Iteration")
            self.matplotlib_axes.set_ylabel("Value")
            self.matplotlib_axes.set_title("Node Values Over Time")
            self.matplotlib_axes.grid(True, alpha=0.3)

            try:
                self.matplotlib_canvas.draw()
            except Exception:
                pass

            self.status_label.setText("Matplotlib backend active")

        def _switch_backend(self, backend: str):
            """Switch between available plotting backends.

            This will remove the existing plot widget (if any) and create the
            requested backend widget.
            """
            # Remove existing widget if present
            if getattr(self, "plot_widget", None):
                try:
                    self.plot_container_layout.removeWidget(self.plot_widget)
                except Exception:
                    pass
                try:
                    self.plot_widget.setParent(None)
                except Exception:
                    pass

                # Clear references
                self.plot_widget = None
                self.pyqtgraph_plot = None
                self.matplotlib_canvas = None
                self.matplotlib_axes = None
                self._line_items.clear()

            # Create selected backend
            if backend == "matplotlib":
                if not MATPLOTLIB_AVAILABLE:
                    self.status_label.setText("Matplotlib not available")
                else:
                    self._create_matplotlib_backend()
            elif backend == "pyqtgraph":
                if not PYQTGRAPH_AVAILABLE:
                    self.status_label.setText("PyQtGraph not available")
                else:
                    self._create_pyqtgraph_backend()
            else:
                self.status_label.setText("Unknown backend")

            # Refresh plot content for new backend
            try:
                self._refresh_plot()
            except Exception:
                pass

        def _refresh_plot(self):
            """Refresh plot with all current data."""
            self._clear_plot()

            # Redraw all nodes
            all_data = self.get_viewmodel().get_all_plot_data()
            for node_name, data_points in all_data.items():
                if data_points:
                    self._plot_node_data(node_name, data_points)

            self._update_node_list()

        def _clear_plot(self):
            """Clear all data from plot."""
            if self.matplotlib_axes:
                self.matplotlib_axes.clear()
                self.matplotlib_axes.set_xlabel("Iteration")
                self.matplotlib_axes.set_ylabel("Value")
                self.matplotlib_axes.set_title("Node Values Over Time")
                self.matplotlib_axes.grid(True, alpha=0.3)
                self.matplotlib_canvas.draw()

            if self.pyqtgraph_plot:
                self.pyqtgraph_plot.clear()

            self._line_items.clear()

        def _plot_node_data(self, node_name: str, data_points: list):
            """Plot data for a specific node.

            Args:
                node_name: Name of the node
                data_points: List of PlotDataPoint objects
            """
            if not data_points:
                return

            iterations = [p.iteration for p in data_points]
            values = [p.value for p in data_points]
            color = self.get_viewmodel().get_node_color(node_name)

            if self.matplotlib_axes:
                (line,) = self.matplotlib_axes.plot(
                    iterations, values, label=node_name, color=color, linewidth=2
                )
                self._line_items[node_name] = line
                self.matplotlib_axes.legend()
                self.matplotlib_canvas.draw()

            if self.pyqtgraph_plot:
                pen = pg.mkPen(color=color, width=2)
                line_item = self.pyqtgraph_plot.plot(
                    iterations, values, pen=pen, name=node_name
                )
                self._line_items[node_name] = line_item

        def _update_node_list(self):
            """Update the node list widget."""
            self.node_list_widget.clear()
            for node_name in self.get_viewmodel().get_plotted_nodes():
                self.node_list_widget.addItem(node_name)

        def _on_backend_changed(self, index: int):
            """Handle backend combo box change."""
            backend = self.backend_combo.itemData(index)
            if backend and backend != self.get_viewmodel().get_backend():
                self.get_viewmodel().set_backend(backend)

        def _on_buffer_size_changed(self, value: int):
            """Handle buffer size spinbox change."""
            self.get_viewmodel().set_buffer_size(value)
            self.status_label.setText(f"Buffer size set to {value}")

        def _on_backend_updated(self, _):
            """Handle backend changed in ViewModel."""
            backend = self.get_viewmodel().get_backend()
            self._switch_backend(backend)

        def _on_data_updated(self, _):
            """Handle data updated in ViewModel."""
            if not self._paused:
                self._refresh_plot()

        def _on_nodes_changed(self, _):
            """Handle nodes changed in ViewModel."""
            self._refresh_plot()

        def _on_clear_clicked(self):
            """Handle clear button click."""
            self.get_viewmodel().clear_data()

        def _on_remove_node_clicked(self):
            """Handle remove node button click."""
            current_item = self.node_list_widget.currentItem()
            if current_item:
                node_name = current_item.text()
                self.get_viewmodel().remove_node(node_name)

        def _on_reset_zoom_clicked(self):
            """Reset zoom to show all data."""
            if self.pyqtgraph_plot:
                self.pyqtgraph_plot.enableAutoRange()
            if self.matplotlib_axes:
                self.matplotlib_axes.relim()
                self.matplotlib_axes.autoscale_view()
                self.matplotlib_canvas.draw()

        def _on_autoscale_changed(self, state):
            """Handle autoscale checkbox change."""
            self._autoscale_y = self.autoscale_check.isChecked()
            if self.pyqtgraph_plot:
                self.pyqtgraph_plot.enableAutoRange(y=self._autoscale_y)

        def _on_pause_changed(self, state):
            """Handle pause checkbox change."""
            self._paused = self.pause_check.isChecked()

        def _on_antialias_changed(self, state):
            """Handle antialiasing checkbox change."""
            if self.pyqtgraph_plot:
                # Redraw curves with new antialiasing setting
                use_aa = self.antialias_check.isChecked()
                for node_name, line_item in self._line_items.items():
                    try:
                        # Get current data and redraw with new antialiasing
                        data_points = (
                            self.get_viewmodel().get_all_plot_data().get(node_name, [])
                        )
                        if data_points:
                            iterations = [p.iteration for p in data_points]
                            values = [p.value for p in data_points]
                            line_item.setData(iterations, values, antialias=use_aa)
                    except Exception:
                        pass

        def _on_track_active_changed(self, state):
            """Handle track active subgraph checkbox change."""
            self._track_active_only = self.track_active_check.isChecked()

        def set_active_subgraph(self, subgraph):
            """Set the currently active subgraph for tracking."""
            self._active_subgraph = subgraph

        def set_iteration(self, iteration: int):
            """Update the iteration label."""
            try:
                self.iteration_label.setText(f"Iteration: {iteration}")
            except Exception:
                pass

        def is_paused(self) -> bool:
            """Check if plot updates are paused."""
            return self._paused

        def update_plot(self):
            """Manual update method for external calls."""
            if not self._paused:
                self._refresh_plot()

else:
    # Stub for testing without PyQt6
    class PlotView:
        def __init__(self, viewmodel, parent=None):
            self.viewmodel = viewmodel

        def update_plot(self):
            pass
