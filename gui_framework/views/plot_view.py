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
                parent: Parent Qt widget
            """
            super().__init__(viewmodel, parent)
            # Backwards compatibility: expose 'viewmodel' attribute
            self.viewmodel = viewmodel
            self.setWindowTitle("Node Values Plot")
            self.resize(900, 600)

            # Plot components
            self.plot_widget = None
            self.matplotlib_canvas = None
            self.matplotlib_axes = None
            self.pyqtgraph_plot = None
            self._line_items = {}  # node_name -> plot item

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
            backend_layout.addStretch()
            layout.addLayout(backend_layout)

            # Plot container (dynamically populated based on backend)
            self.plot_container_layout = QVBoxLayout()
            layout.addLayout(self.plot_container_layout)

            # Controls (bottom)
            controls_layout = QHBoxLayout()

            self.clear_button = QPushButton("Clear")
            self.clear_button.clicked.connect(self._on_clear_clicked)
            controls_layout.addWidget(self.clear_button)

            self.node_list_widget = QListWidget()
            self.node_list_widget.setMaximumHeight(120)
            self.node_list_widget.setSelectionMode(
                QListWidget.SelectionMode.SingleSelection
            )

            controls_layout.addWidget(QLabel("Plotted Nodes:"))
            controls_layout.addWidget(self.node_list_widget)

            self.remove_node_button = QPushButton("Remove Selected")
            self.remove_node_button.clicked.connect(self._on_remove_node_clicked)
            controls_layout.addWidget(self.remove_node_button)

            layout.addLayout(controls_layout)

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

        def _on_backend_updated(self, _):
            """Handle backend changed in ViewModel."""
            backend = self.get_viewmodel().get_backend()
            self._switch_backend(backend)

        def _on_data_updated(self, _):
            """Handle data updated in ViewModel."""
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

        def update_plot(self):
            """Manual update method for external calls."""
            self._refresh_plot()

else:
    # Stub for testing without PyQt6
    class PlotView:
        def __init__(self, viewmodel, parent=None):
            self.viewmodel = viewmodel

        def update_plot(self):
            pass
