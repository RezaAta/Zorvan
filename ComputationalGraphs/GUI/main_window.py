"""
Main window for the ComputationalGraphs visual editor.
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QUndoStack
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ComputationalGraphs.Core.Graph import Graph

from .combined_node_palette import CombinedNodePalette

# Import refactored controllers
from .controllers import (
    ConsoleController,
    ControlPanelBuilder,
    DialogController,
    ExecutionController,
    ExecutionSettingsController,
    FileIOController,
    GraphBuilderController,
    GraphEdgeController,
    GraphLayoutController,
    MenuToolbarController,
    NodeEditingController,
    NodeSequenceController,
    PlottingController,
    SearchController,
    VisualizationController,
)
from .examples_loader import ExamplesLoader
from .graph_canvas import GraphCanvas
from .graph_runner import GraphRunner

logger = logging.getLogger(__name__)

# Import plot_window early to init PyQtGraph config
from .plot_window import PlotConfigDialog, create_plot_window  # noqa: F401


class CollapsibleSection(QWidget):
    """A simple collapsible section widget with a header button.

    The header is a checkable QToolButton that toggles visibility of the
    provided content widget. Keeps layout margins consistent.
    """

    def __init__(self, title: str, content_widget: QWidget, expanded: bool = True):
        super().__init__()
        self.toggle_button = QToolButton()
        try:
            self.toggle_button.setProperty("themed", True)
            self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.toggle_button.setMouseTracking(True)
        except Exception:
            pass
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(expanded)
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        # Make header occupy the full horizontal width and style the active state
        self.toggle_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        # Apply initial style from theme (header color for checked state)
        try:
            from .theme import get_theme_manager

            tm = get_theme_manager()
            header = tm.get_color("header_bg", "#239483").name()
            txt = tm.get_color("text").name()
            self.toggle_button.setStyleSheet(
                f"QToolButton {{ text-align: left; padding: 6px 8px; border-radius: 6px; font-weight: bold; }} "
                f"QToolButton:checked {{ background-color: {header}; color: {txt}; }} "
            )
            # update style when theme changes
            tm.theme_changed.connect(self._on_theme_changed)
        except Exception:
            self.toggle_button.setStyleSheet(
                "QToolButton { text-align: left; padding: 6px 8px; border-radius: 6px; font-weight: bold; } "
                "QToolButton:checked { background-color: #239483; color: #dcdcdc; }"
            )
        # Ensure arrow and text align nicely and font weight is clear
        self.toggle_button.setFont(
            QFont(
                self.toggle_button.font().family(),
                self.toggle_button.font().pointSize(),
                QFont.Weight.Bold,
            )
        )
        # Use small arrow to indicate expand/collapse
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        )

        self.content = content_widget

        # Layout
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.toggle_button)
        v.addWidget(self.content)

        # Connect
        self.toggle_button.toggled.connect(self.on_toggled)
        # Ensure content visibility matches initial expanded flag
        try:
            self.content.setVisible(self.toggle_button.isChecked())
        except Exception:
            pass
        # Theme change handler
        try:
            tm
        except Exception:
            tm = None

    def _on_theme_changed(self):
        """Update toggle button style when theme changes."""
        try:
            from .theme import get_theme_manager

            tm = get_theme_manager()
            header = tm.get_color("header_bg", "#239483").name()
            txt = tm.get_color("text").name()
            self.toggle_button.setStyleSheet(
                f"QToolButton {{ text-align: left; padding: 6px 8px; border-radius: 6px; font-weight: bold; }} "
                f"QToolButton:checked {{ background-color: {header}; color: {txt}; }} "
            )
        except Exception:
            pass

    def on_toggled(self, checked: bool):
        self.content.setVisible(checked)
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )


class MainWindow(QMainWindow):
    """Main application window for the graph editor."""

    console_write = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Set a consistent application font for UI (adjustable via Preferences)
        try:
            from PyQt6.QtGui import QFont

            from .theme import get_theme_manager

            tm = get_theme_manager()
            ui_font = tm.get_font("ui")
            QApplication.setFont(ui_font)
            # Ensure runtime updates to UI font are applied
            tm.theme_changed.connect(lambda: QApplication.setFont(tm.get_font("ui")))
        except Exception:
            # If QApplication not available or font fails, ignore silently
            pass

        self.setWindowTitle("Computational Graphs Visual Editor")
        self.resize(1200, 800)

        # Undo/Redo stack for UI actions
        self.undo_stack = QUndoStack(self)

        # Initialize custom node manager early (before UI setup)
        try:
            from ComputationalGraphs.GUI.custom_node_manager import (
                get_custom_node_manager,
            )

            self.custom_node_manager = get_custom_node_manager()
            self.custom_node_manager.register_with_factory()
        except Exception as e:
            logger.warning("Failed to initialize custom node manager: %s", e)
            self.custom_node_manager = None

        # Core components
        # Create a new Graph object and use set_graph to keep everything in sync
        new_graph = Graph()
        logger.debug("MainWindow: Graph created")
        self.graph_runner = GraphRunner(self)
        logger.debug("MainWindow: GraphRunner created")
        # Ensure runner and canvas reference the authoritative graph (use set_graph)
        try:
            self.set_graph(new_graph)
            logger.debug("MainWindow: set_graph successful")
        except Exception:
            # If set_graph is not yet available, fallback to direct assignment
            self.graph = new_graph
            self.graph_runner.set_graph(self.graph)
            logger.debug("MainWindow: set_graph fallback used")
        # Examples: legacy loader + modern repository (for programmatic builders)
        try:
            from gui_framework.services.examples_repository import ExamplesRepository

            self.examples_repository = ExamplesRepository()
        except Exception:
            self.examples_repository = None

        self.examples_loader = ExamplesLoader()
        logger.debug("MainWindow: ExamplesLoader created")

        # Connect signals
        self.graph_runner.step_completed.connect(self.on_step_completed)
        self.graph_runner.execution_finished.connect(self.on_execution_finished)
        self.graph_runner.error_occurred.connect(self.on_error)
        logger.debug("MainWindow: connected graph_runner signals")

        # Initialize controllers (refactored from monolithic methods)
        self.execution_controller = ExecutionController(self)
        self.file_io_controller = FileIOController(self)
        self.search_controller = SearchController(self)
        self.visualization_controller = VisualizationController(self)
        self.node_sequence_controller = NodeSequenceController(self)
        self.plotting_controller = PlottingController(self)
        self.graph_builder_controller = GraphBuilderController(self)
        self.dialog_controller = DialogController(self)
        self.graph_layout_controller = GraphLayoutController(self)
        self.execution_settings_controller = ExecutionSettingsController(self)
        self.graph_edge_controller = GraphEdgeController(self)
        self.node_editing_controller = NodeEditingController(self)
        self.console_controller = ConsoleController(self)
        self.menu_toolbar_controller = MenuToolbarController(self)
        self.control_panel_builder = ControlPanelBuilder(self)

        # === MVVM Integration ===
        # Initialize MVVM adapters for incremental migration from legacy controllers
        self._init_mvvm_adapters()

        # State (must be before init_ui)
        self.colorize_enabled = False
        self.min_value_range = 0.0  # Numeric min value
        self.max_value_range = 1.0  # Numeric max value
        # Load persisted visualization preferences if available
        try:
            from .theme import get_theme_manager

            tm = get_theme_manager()
            min_col = tm.settings.value("visualization/min_gradient_color", None)
            max_col = tm.settings.value("visualization/max_gradient_color", None)
            node_col = tm.settings.value("visualization/default_node_color", None)
            text_col = tm.settings.value("visualization/default_text_color", None)
        except Exception:
            min_col = max_col = node_col = text_col = None

        self.min_gradient_color = (
            QColor(min_col) if min_col else QColor(0, 0, 255)
        )  # Blue for minimum
        self.max_gradient_color = (
            QColor(max_col) if max_col else QColor(255, 0, 0)
        )  # Red for maximum
        self.skip_visualization = False  # Skip graph canvas updates
        self.skip_plotting = False  # Skip plot window updates
        self.saved_speed = 500  # For max speed toggle
        # ANN coloring state (checkbox)
        self.ann_colors_enabled = False

        # Default node/text colors (may have been persisted)
        self.default_node_color = (
            QColor(node_col) if node_col else QColor(100, 150, 200)
        )
        self.default_text_color = (
            QColor(text_col) if text_col else QColor(255, 255, 255)
        )

        # Plot window
        self.plot_window = None

        # === Multi-Graph Support: Selected graph for processing ===
        self.selected_processing_graph = None  # None = use mother graph (all nodes)

        self.init_ui()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_status_bar()

        # Ensure persisted color preferences are fully applied to widgets
        # that registered theme handlers during initialization (dock backgrounds,
        # icon reapply handlers, etc.). Some components register listeners
        # during controller construction, so re-applying the theme here guarantees
        # those handlers run at startup as well.
        try:
            from .theme import get_theme_manager

            tm = get_theme_manager()
            try:
                # Defer actual application until after initialization to avoid
                # interacting with widgets that are still being constructed.
                try:
                    from PyQt6.QtCore import QTimer

                    QTimer.singleShot(0, tm.apply_theme)
                except Exception:
                    # Fall back to immediate application when QTimer isn't available
                    try:
                        tm.apply_theme()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

        # Refresh dock backgrounds if control panel provided the helper
        try:
            if hasattr(self, "refresh_dock_backgrounds"):
                try:
                    self.refresh_dock_backgrounds()
                except Exception:
                    pass
        except Exception:
            pass

        # Re-run any registered icon reapply handlers so icons pick up accent
        # colors when the handlers were registered after the initial theme
        # application during startup.
        try:
            from .controllers.control_panel_builder import _ICON_REAPPLY_HANDLERS

            for h in list(_ICON_REAPPLY_HANDLERS):
                try:
                    h()
                except Exception:
                    pass
        except Exception:
            pass

        # Apply visualization defaults immediately so the UI reflects persisted
        # or initial default colors without requiring the user to press Apply.
        try:
            try:
                # Ensure color buttons show current color values
                self.min_color_btn.setStyleSheet(
                    f"background-color: {self.min_gradient_color.name()};"
                )
                self.max_color_btn.setStyleSheet(
                    f"background-color: {self.max_gradient_color.name()};"
                )
                self.node_color_btn.setStyleSheet(
                    f"background-color: {self.default_node_color.name()};"
                )
                self.text_color_btn.setStyleSheet(
                    f"background-color: {self.default_text_color.name()};"
                )
            except Exception:
                pass

            # Apply colors to nodes if any exist on canvas
            try:
                self.visualization_controller.apply_node_colors()
            except Exception:
                pass
        except Exception:
            pass

    def _init_mvvm_adapters(self):
        """Initialize MVVM adapters for incremental migration from legacy controllers.

        This method sets up the bridge between the new MVVM architecture and
        the legacy controller-based system, enabling gradual migration.
        """
        # Initialize execution adapter (bridges ExecutionViewModel with GraphRunner)
        try:
            from gui_framework.adapters.execution_adapter import ExecutionAdapter

            self.execution_adapter = ExecutionAdapter(self)
            self.execution_adapter.connect()
            logger.debug("MainWindow: ExecutionAdapter initialized")
        except Exception as e:
            logger.warning("Failed to initialize ExecutionAdapter: %s", e)
            self.execution_adapter = None

        # Initialize file I/O adapter (bridges FileIOViewModel with FileIOController)
        try:
            from gui_framework.adapters.file_io_adapter import FileIOAdapter

            self.file_io_adapter = FileIOAdapter(self)
            self.file_io_adapter.connect()
            logger.debug("MainWindow: FileIOAdapter initialized")
        except Exception as e:
            logger.warning("Failed to initialize FileIOAdapter: %s", e)
            self.file_io_adapter = None

        # Initialize theme adapter (bridges ThemeViewModel with legacy ThemeManager)
        try:
            from gui_framework.adapters.theme_adapter import ThemeAdapter

            self.theme_adapter = ThemeAdapter()
            # Sync initial theme from legacy to MVVM
            self.theme_adapter.sync_legacy_to_state_store()
            # Enable bidirectional sync
            self.theme_adapter.start_bidirectional_sync()
            # Store viewmodel reference for convenience
            self.theme_vm = self.theme_adapter._theme_viewmodel
            logger.debug("MainWindow: ThemeAdapter initialized with bidirectional sync")
        except Exception as e:
            logger.warning("Failed to initialize ThemeAdapter: %s", e)
            self.theme_adapter = None
            self.theme_vm = None

        # Initialize palette adapter (bridges CombinedNodePaletteViewModel with legacy palette)
        try:
            from gui_framework.adapters.palette_adapter import PaletteAdapter

            self.palette_adapter = PaletteAdapter(self)
            self.palette_adapter.connect()
            # Store viewmodel reference for convenience
            self.palette_vm = self.palette_adapter.viewmodel
            logger.debug("MainWindow: PaletteAdapter initialized")
        except Exception as e:
            logger.warning("Failed to initialize PaletteAdapter: %s", e)
            self.palette_adapter = None
            self.palette_vm = None

        # Initialize examples loader adapter (bridges ExamplesLoaderViewModel with legacy loader)
        try:
            from gui_framework.adapters.examples_loader_adapter import (
                ExamplesLoaderAdapter,
            )

            self.examples_loader_adapter = ExamplesLoaderAdapter(self)
            self.examples_loader_adapter.connect()
            # Store viewmodel reference for convenience
            self.examples_loader_vm = self.examples_loader_adapter.viewmodel
            logger.debug("MainWindow: ExamplesLoaderAdapter initialized")
        except Exception as e:
            logger.warning("Failed to initialize ExamplesLoaderAdapter: %s", e)
            self.examples_loader_adapter = None
            self.examples_loader_vm = None

        # Initialize layouts adapter (bridges LayoutsView with GraphLayoutController)
        try:
            from gui_framework.adapters.layouts_adapter import LayoutsAdapter

            self.layouts_adapter = LayoutsAdapter(self)
            self.layouts_adapter.connect()
            logger.debug("MainWindow: LayoutsAdapter initialized")
        except Exception as e:
            logger.warning("Failed to initialize LayoutsAdapter: %s", e)
            self.layouts_adapter = None

        # Initialize dialogs adapter (bridges MVVM dialogs with DialogController)
        try:
            from gui_framework.adapters.dialogs_adapter import DialogsAdapter

            self.dialogs_adapter = DialogsAdapter(self)
            self.dialogs_adapter.connect()
            logger.debug("MainWindow: DialogsAdapter initialized")
        except Exception as e:
            logger.warning("Failed to initialize DialogsAdapter: %s", e)
            self.dialogs_adapter = None

        # Initialize plot adapter (bridges PlotView with legacy PlotWindow)
        try:
            from gui_framework.adapters.plot_adapter import PlotAdapter

            self.plot_adapter = PlotAdapter(parent=self)
            logger.debug("MainWindow: PlotAdapter initialized")
        except Exception as e:
            logger.warning("Failed to initialize PlotAdapter: %s", e)
            self.plot_adapter = None

    def set_graph(self, graph: Graph):
        """Set the authoritative Graph instance and keep canvas and runner in sync.

        This helps avoid stale references where UI actions affect a different graph
        object than the one used for processing.
        """
        self.graph = graph

        # Mark as mother graph for multi-graph support
        try:
            graph.set_as_mother_graph()
        except Exception:
            pass

        try:
            self.canvas.graph = graph
        except Exception:
            pass
        try:
            # GraphRunner expects set_graph to be called so it uses the same graph
            if (
                hasattr(self, "graph_runner")
                and getattr(self, "graph_runner") is not None
            ):
                self.graph_runner.set_graph(graph)
        except Exception:
            pass

        # Ensure CanvasViewModel is available and in sync for the Inspector
        try:
            from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel

            # Create or update canvas viewmodel to reflect new graph
            if not hasattr(self, "canvas_vm") or self.canvas_vm is None:
                self.canvas_vm = CanvasViewModel(graph)
                try:
                    self.canvas_vm.initialize()
                except Exception:
                    pass
            else:
                try:
                    self.canvas_vm.load_graph(graph)
                except Exception:
                    # Recreate if load_graph fails
                    try:
                        self.canvas_vm = CanvasViewModel(graph)
                        self.canvas_vm.initialize()
                    except Exception:
                        pass

            # Connect selection synchronization (single-time only)
            try:
                if not getattr(self, "_inspector_selection_connected", False):
                    self.canvas.scene.selectionChanged.connect(
                        lambda: self._on_canvas_selection_changed()
                    )
                    self._inspector_selection_connected = True
            except Exception:
                pass
        except Exception:
            pass

        # Update displayed starting/stopping nodes
        try:
            self.update_starting_nodes_display()
            self.update_stopping_nodes_display()
        except Exception:
            pass
        # Update graph selector dropdown
        try:
            self.update_graph_selector()
        except Exception:
            pass

        # Reapply visualization overlays/preferences for the new graph
        try:
            # If ANN coloring is enabled, ensure canvas applies ANN colors for the new nodes
            if getattr(self, "ann_colors_enabled", False):
                try:
                    self.visualization_controller.canvas.apply_ann_colors()
                except Exception:
                    pass
            # If colorize-by-value is enabled, re-detect range and update visuals
            elif getattr(self, "colorize_enabled", False):
                try:
                    self.visualization_controller.auto_detect_range()
                except Exception:
                    pass
        except Exception:
            pass

    def init_ui(self):
        """Initialize the UI components."""
        # Central widget - Graph Canvas
        self.canvas = GraphCanvas(self)
        # Provide canvas with a pointer to the underlying computational Graph
        try:
            self.canvas.graph = self.graph
        except Exception:
            pass
        # Provide canvas with a reference to main_window for subgraph control updates
        try:
            self.canvas.main_window = self
        except Exception:
            pass
        # Default grid & snap settings (recommended)
        try:
            self.canvas.set_grid_mode("4x4")
            self.canvas.set_snap_to_grid(True)
            # Default: enable snap while dragging so snap is visible
            self.canvas.set_snap_while_dragging(True)
            # Default: show the grid
            self.canvas.set_show_grid(True)
        except Exception:
            pass
        self.canvas.edge_created.connect(self.on_edge_created)
        # Handle connection released on empty canvas - create node and connect
        try:
            self.canvas.connection_dropped_on_empty.connect(
                self.node_editing_controller.create_node_from_drop
            )
        except Exception:
            pass
        self.canvas.edge_removed.connect(self.on_edge_removed)
        self.setCentralWidget(self.canvas)

        # Left dock - Combined Node Palette (default)
        try:
            self.combined_palette = CombinedNodePalette(self)
            self.combined_palette.setVisible(True)
            self.addDockWidget(
                Qt.DockWidgetArea.LeftDockWidgetArea, self.combined_palette
            )
            # Expose under the legacy attribute name for compatibility
            self.palette = self.combined_palette
        except Exception:
            # If instantiation fails, still continue - UI will operate without palette
            self.combined_palette = None
            self.palette = None

        # Ensure create custom node action is handled regardless of palette implementation
        try:

            def _open_custom_node_dialog():
                # Try MVVM-based adapter first, fallback to legacy dialog
                try:
                    from ComputationalGraphs.GUI.custom_node_dialog_adapter import (
                        CustomNodeDialogAdapter,
                    )

                    # Pass a minimal "node-like" object to the adapter
                    class _NodeLike:
                        pass

                    dlg = CustomNodeDialogAdapter(_NodeLike(), parent=self)
                    dlg.exec()
                    return
                except Exception:
                    pass

                try:
                    from ComputationalGraphs.GUI.custom_node_dialog import (
                        CustomNodeDialog,
                    )

                    dlg = CustomNodeDialog(parent=self)
                    dlg.exec()
                except Exception:
                    pass

            # If palette implements the adapter-style handler registration, use it
            try:
                if self.combined_palette is not None and hasattr(
                    self.combined_palette, "add_create_handler"
                ):
                    try:
                        self.combined_palette.add_create_handler(
                            _open_custom_node_dialog
                        )
                    except Exception:
                        pass
            except Exception:
                pass

            # Otherwise, hook into visible create button(s) on the palette
            try:
                pal = self.combined_palette or self.palette
                if pal is not None:
                    if hasattr(pal, "create_btn"):
                        try:
                            pal.create_btn.clicked.connect(_open_custom_node_dialog)
                        except Exception:
                            pass
                    if hasattr(pal, "create_custom_button"):
                        try:
                            pal.create_custom_button.clicked.connect(
                                _open_custom_node_dialog
                            )
                        except Exception:
                            pass
            except Exception:
                pass
        except Exception:
            pass

        # Right dock - Controls
        self.create_control_panel()
        # Inspector panel (dock) - node properties
        try:
            self.create_inspector_panel()
        except Exception:
            pass
        # Bottom dock - Console for verbose/debug output
        self.create_console_panel()

    def create_control_panel(self):
        """Create the control panel dock. Delegated to ControlPanelBuilder."""
        self.control_panel_builder.build()

    def create_actions(self):
        """Create menu actions. Delegated to MenuToolbarController."""
        self.menu_toolbar_controller.create_actions()

    def create_menus(self):
        """Create menu bar. Delegated to MenuToolbarController."""
        self.menu_toolbar_controller.create_menus()

    def create_toolbars(self):
        """Create toolbars. Delegated to MenuToolbarController."""
        self.menu_toolbar_controller.create_toolbars()

    def create_status_bar(self):
        """Create status bar. Delegated to MenuToolbarController."""
        self.menu_toolbar_controller.create_status_bar()

    def create_console_panel(self):
        """Create console panel. Delegated to ConsoleController."""
        self.console_controller.create_console_panel()

    def _on_canvas_selection_changed(self):
        """Sync selection from GraphCanvas to CanvasViewModel so Inspector updates."""
        try:
            if not hasattr(self, "canvas_vm") or self.canvas_vm is None:
                return
            # Pick first selected node item
            selected = [
                it for it in self.canvas.scene.selectedItems() if hasattr(it, "node")
            ]
            if not selected:
                try:
                    self.canvas_vm.clear_selection()
                except Exception:
                    pass
                # Clear inspector view
                try:
                    if (
                        hasattr(self, "inspector_pane")
                        and self.inspector_pane is not None
                    ):
                        try:
                            self.inspector_pane.get_viewmodel()._load_properties_for(
                                None
                            )
                        except Exception:
                            try:
                                self.inspector_pane.get_viewmodel().properties_changed += (
                                    1
                                )
                            except Exception:
                                pass
                except Exception:
                    pass
                return
            first = selected[0]
            try:
                node_id = getattr(first.node, "name", None)
                if node_id:
                    try:
                        self.canvas_vm.select_node(node_id)
                    except Exception:
                        pass
                    # Force-inspector refresh in case selection->render state mapping isn't fully synchronized
                    try:
                        if (
                            hasattr(self, "inspector_pane")
                            and self.inspector_pane is not None
                        ):
                            try:
                                # Call internal loader for immediate update (deterministic for UI)
                                self.inspector_pane.get_viewmodel()._load_properties_for(
                                    node_id
                                )
                            except Exception:
                                # Fallback: bump properties_changed to trigger view update
                                try:
                                    self.inspector_pane.get_viewmodel().properties_changed += (
                                        1
                                    )
                                except Exception:
                                    pass
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def create_inspector_panel(self):
        """Create a dockable Inspector that binds to CanvasViewModel."""
        try:
            from PyQt6.QtCore import Qt
            from PyQt6.QtWidgets import QDockWidget

            from .inspector_pane import InspectorPane

            # Ensure canvas_vm exists
            if not hasattr(self, "canvas_vm") or self.canvas_vm is None:
                from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel

                self.canvas_vm = CanvasViewModel(self.graph)
                try:
                    self.canvas_vm.initialize()
                except Exception:
                    pass

            pane = InspectorPane(self.canvas_vm, self)
            # Keep a reference so we can directly refresh the inspector when selection changes
            self.inspector_pane = pane
            dock = QDockWidget("Inspector", self)
            dock.setAllowedAreas(
                Qt.DockWidgetArea.RightDockWidgetArea
                | Qt.DockWidgetArea.LeftDockWidgetArea
            )
            dock.setWidget(pane.widget())
            # Create dock but keep it hidden/closed by default (user may open from View menu)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            dock.hide()
            self.inspector_dock = dock
        except Exception as e:
            # Fail silently but log if possible
            try:
                import logging

                logging.getLogger(__name__).exception(
                    "Failed to create inspector panel: %s", e
                )
            except Exception:
                pass

    def write_to_console(self, message: str, verbose_only: bool = False):
        """Write to console. Delegated to ConsoleController."""
        self.console_controller.write_to_console(message, verbose_only)

    # Graph operations - delegated to FileIOController

    def new_graph(self):
        """Create a new empty graph."""
        self.file_io_controller.new_graph()

    def open_graph(self):
        """Open a graph from file."""
        self.file_io_controller.open_graph()

    def save_graph(self):
        """Save the current graph to file."""
        self.file_io_controller.save_graph()

    def save_selection_as_graph(self):
        """Save selected nodes as a new graph file (Phase 3)."""
        self.file_io_controller.save_selection_as_graph()

    def import_graph_to_canvas(self):
        """Import a graph file and merge it into current canvas (Phase 3)."""
        self.file_io_controller.import_graph_to_canvas()

    def create_subgraph_from_selection(self):
        """Create a sub-graph from the currently selected nodes (Phase 3)."""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox

        selected_items = [
            item for item in self.canvas.scene.selectedItems() if hasattr(item, "node")
        ]

        if not selected_items:
            QMessageBox.warning(
                self, "No Selection", "Please select nodes to group into a sub-graph."
            )
            return

        # Get the actual node objects
        nodes = [item.node for item in selected_items]

        # Prompt for sub-graph name
        name, ok = QInputDialog.getText(
            self,
            "Create Sub-Graph",
            "Enter a name for the sub-graph:",
            text=f"Sub-Graph {len(getattr(self.graph, 'sub_graphs', [])) + 1}",
        )

        if not ok or not name.strip():
            return

        # Create the sub-graph
        try:
            subgraph = self.graph.create_subgraph_from_nodes(nodes, name.strip())
            if subgraph:
                # Refresh the canvas to show the visual grouping
                self.canvas.refresh_subgraph_visuals()

                # Update the graph selector dropdown
                self.update_graph_selector()

                # Notify via on_subgraph_created if available
                if hasattr(self, "on_subgraph_created"):
                    self.on_subgraph_created(subgraph)

                QMessageBox.information(
                    self,
                    "Sub-Graph Created",
                    f"Sub-graph '{name}' created with {len(nodes)} nodes.",
                )
        except ValueError as e:
            QMessageBox.warning(self, "Cannot Create Sub-Graph", str(e))

    def edit_node(self, node_item):
        """Open editor dialog for a specific node item. Delegated to NodeEditingController."""
        self.node_editing_controller.edit_node(node_item)

    def replace_node(self, node_item):
        """Replace node type. Delegated to NodeEditingController."""
        self.node_editing_controller.replace_node(node_item)

    def edit_selected_node(self):
        """Open editor for the selected node. Delegated to NodeEditingController."""
        self.node_editing_controller.edit_selected_node()

    def inspect_selected_node(self):
        """Open inspector for the selected node. Delegated to NodeEditingController."""
        self.node_editing_controller.inspect_selected_node()

    def show_preferences(self):
        """Show color/theme preferences dialog."""
        try:
            # Use the ComputationalGraphs adapter which delegates to the MVVM dialog
            # and exposes the full set of controls (fonts, accent, node colors, etc.).
            from .color_preferences import ColorPreferencesDialog

            dlg = ColorPreferencesDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Preferences", f"Unable to open preferences: {e}")

    # Execution controls - delegated to ExecutionController

    def play_graph(self):
        """Start graph execution."""
        self.execution_controller.play()

    def run_batch_mode(self, max_steps):
        """Run all steps at once without updating visuals until complete."""
        self.execution_controller.run_batch_mode(max_steps)

    def pause_graph(self):
        """Pause graph execution."""
        self.execution_controller.pause()

    def resume_graph(self):
        """Resume a paused background execution."""
        self.execution_controller.resume()

    def step_graph(self):
        """Execute a single step."""
        self.execution_controller.step()

    def reset_graph(self):
        """Reset graph execution."""
        self.execution_controller.reset()

    def restore_graph(self):
        """Restore graph to iteration 0 state without changing iteration counter."""
        self.execution_controller.restore_graph()

    def reset_processor(self):
        """Reset only the processor and iteration counter, preserving node values."""
        self.execution_controller.reset_processor()

    # === Phase 2: Processing Queue Methods ===

    def add_selected_graph_to_queue(self):
        """Add the currently selected graph/subgraph to the processing queue."""
        # Get the currently selected graph from the dropdown
        selected_graph = self.get_selected_processing_graph()
        iterations = self.queue_iterations_spin.value()

        if selected_graph is None:
            selected_graph = self.graph  # Default to mother graph

        self.graph_runner.add_to_queue(selected_graph, iterations)
        self._update_queue_display()
        self.status_bar.showMessage(
            f"Added '{self._get_graph_display_name(selected_graph)}' "
            f"({iterations} iterations) to queue"
        )

    def get_selected_processing_graph(self):
        """Get the graph/subgraph currently selected in the dropdown."""
        if not hasattr(self, "graph_selector_combo"):
            return self.graph

        index = self.graph_selector_combo.currentIndex()
        if index <= 0:  # "Mother Graph (All)" or nothing
            return self.graph

        # Get subgraphs
        sub_graphs = getattr(self.graph, "sub_graphs", [])
        if index - 1 < len(sub_graphs):
            return sub_graphs[index - 1]
        return self.graph

    def _get_graph_display_name(self, graph):
        """Get a display name for a graph."""
        if graph == self.graph:
            return "Mother Graph"
        return getattr(graph, "graph_name", "SubGraph")

    def start_processing_queue(self):
        """Start processing the queue."""
        if not self.graph_runner.get_queue():
            self.status_bar.showMessage("Queue is empty")
            return

        # Connect to queue signals
        try:
            self.graph_runner.queue_item_started.disconnect()
            self.graph_runner.queue_item_finished.disconnect()
            self.graph_runner.queue_finished.disconnect()
        except Exception:
            pass

        self.graph_runner.queue_item_started.connect(self._on_queue_item_started)
        self.graph_runner.queue_item_finished.connect(self._on_queue_item_finished)
        self.graph_runner.queue_finished.connect(self._on_queue_finished)

        # Set repeat mode from checkbox and spinbox
        repeat_check = getattr(self, "queue_repeat_check", None)
        repeat_spin = getattr(self, "queue_repeat_spin", None)
        if repeat_check is not None and repeat_spin is not None:
            if repeat_check.isChecked():
                # 0 = infinite, N = repeat N times
                self.graph_runner.set_queue_repeat(True, repeat_spin.value())
            else:
                self.graph_runner.set_queue_repeat(False, 0)

        # Update UI state
        self.start_queue_btn.setEnabled(False)
        self.stop_queue_btn.setEnabled(True)

        self.graph_runner.start_queue()

    def stop_processing_queue(self):
        """Stop the processing queue."""
        self.graph_runner.stop_queue()
        self.start_queue_btn.setEnabled(True)
        self.stop_queue_btn.setEnabled(False)
        self.queue_status_label.setText("Queue: Stopped")

    def on_queue_repeat_changed(self, state):
        """Handle repeat checkbox state change."""
        enabled = state == 2  # Qt.CheckState.Checked
        if hasattr(self, "queue_repeat_spin"):
            self.queue_repeat_spin.setEnabled(enabled)

    def _on_queue_item_started(self, graph, iterations):
        """Handle queue item starting."""
        name = self._get_graph_display_name(graph)
        self.queue_status_label.setText(f"Running: {name} ({iterations} iters)")
        self._update_queue_display()

    def _on_queue_item_finished(self, graph, iterations):
        """Handle queue item finishing."""
        name = self._get_graph_display_name(graph)
        self.status_bar.showMessage(f"Completed: {name} ({iterations} iterations)")

    def _on_queue_finished(self):
        """Handle entire queue finishing."""
        self.start_queue_btn.setEnabled(True)
        self.stop_queue_btn.setEnabled(False)
        self.queue_status_label.setText("Queue: Complete")
        self.status_bar.showMessage("Processing queue completed")

    def remove_selected_from_queue(self):
        """Remove the selected item from the queue."""
        if not hasattr(self, "queue_list"):
            return
        row = self.queue_list.currentRow()
        if row >= 0:
            self.graph_runner.remove_from_queue(row)
            self._update_queue_display()

    def clear_processing_queue(self):
        """Clear the processing queue."""
        self.graph_runner.clear_queue()
        self._update_queue_display()
        self.queue_status_label.setText("Queue: Empty")

    def _update_queue_display(self):
        """Update the queue list widget."""
        if not hasattr(self, "queue_list"):
            return

        self.queue_list.clear()
        queue = self.graph_runner.get_queue()

        for i, (graph, iterations) in enumerate(queue):
            name = self._get_graph_display_name(graph)
            self.queue_list.addItem(f"{i + 1}. {name} - {iterations} iterations")

        if queue:
            self.queue_status_label.setText(f"Queue: {len(queue)} item(s)")
        else:
            self.queue_status_label.setText("Queue: Empty")

    # === Phase 2: Per-Graph Reset Methods ===

    def save_selected_graph_snapshot(self):
        """Save a snapshot of the selected graph/subgraph."""
        selected_graph = self.get_selected_processing_graph()
        if selected_graph is None:
            selected_graph = self.graph

        self.graph_runner.save_graph_snapshot_for(selected_graph)
        name = self._get_graph_display_name(selected_graph)
        self.status_bar.showMessage(f"Saved snapshot for '{name}'")

    def reset_selected_graph(self):
        """Reset the selected graph/subgraph to its snapshot."""
        selected_graph = self.get_selected_processing_graph()
        if selected_graph is None:
            selected_graph = self.graph

        self.graph_runner.reset_graph(selected_graph)
        name = self._get_graph_display_name(selected_graph)
        self.status_bar.showMessage(f"Reset '{name}' to snapshot")

        # Update canvas visuals
        try:
            self.canvas.viewport().update()
        except Exception:
            pass

    def rebuild_graph(self):
        """Rebuild the graph from canvas nodes and edges. Delegated to GraphEdgeController."""
        self.graph_edge_controller.rebuild_graph()

    # Event handlers - delegated to ExecutionController

    def on_step_completed(self, step):
        """Handle step completion."""
        self.execution_controller.on_step_completed(step)

    def on_execution_finished(self):
        """Handle execution completion."""
        self.execution_controller.on_execution_finished()

    def on_error(self, message):
        """Handle execution error."""
        self.execution_controller.on_error(message)

    # Speed and execution settings - delegated to ExecutionSettingsController

    def on_speed_changed(self, value):
        """Handle speed slider change. Delegated to ExecutionSettingsController."""
        self.execution_settings_controller.on_speed_changed(value)

    def on_speed_spin_changed(self, value):
        """Handle speed spinbox change. Delegated to ExecutionSettingsController."""
        self.execution_settings_controller.on_speed_spin_changed(value)

    def on_max_speed_toggled(self, checked):
        """Handle max speed button toggle. Delegated to ExecutionSettingsController."""
        self.execution_settings_controller.on_max_speed_toggled(checked)

    def on_skip_viz_changed(self, state):
        """Handle skip graph visualization checkbox change."""
        self.visualization_controller.on_skip_viz_changed(state)

    def on_skip_plot_changed(self, state):
        """Handle skip plot updates checkbox change."""
        self.visualization_controller.on_skip_plot_changed(state)

    def on_verbose_changed(self, state):
        """Handle verbose checkbox change. Delegated to ExecutionSettingsController."""
        self.execution_settings_controller.on_verbose_changed(state)

    def on_dim_processed_changed(self, state):
        """Handle dim-processed checkbox change."""
        self.visualization_controller.on_dim_processed_changed(state)

    def on_colorize_changed(self, state):
        """Handle colorize checkbox change."""
        self.visualization_controller.on_colorize_changed(state)

    def on_ann_color_changed(self, state):
        """Handle ANN color mode checkbox changes. Delegates to visualization controller."""
        self.visualization_controller.on_ann_color_changed(state)

    def on_topology_labels_changed(self, state):
        """Handle topology labels checkbox changes. Delegates to visualization controller."""
        self.visualization_controller.on_topology_labels_changed(state)

    def auto_detect_range(self):
        """Automatically detect min and max values from current node values."""
        self.visualization_controller.auto_detect_range()

    def choose_min_color(self):
        """Choose color for minimum values."""
        self.visualization_controller.choose_min_color()

    def choose_max_color(self):
        """Choose color for maximum values."""
        self.visualization_controller.choose_max_color()

    def on_edge_created(self, source_node, target_node):
        """Handle edge creation. Delegated to GraphEdgeController."""
        self.graph_edge_controller.on_edge_created(source_node, target_node)

    def update_starting_nodes_display(self):
        """Update the starting nodes list display."""
        self.node_sequence_controller.update_starting_nodes_display()

    def add_selected_to_starting_nodes(self):
        """Add selected nodes from canvas to starting nodes list."""
        self.node_sequence_controller.add_selected_to_starting_nodes()

    def on_edge_removed(self, source_node, target_node):
        """Handle edge removal. Delegated to GraphEdgeController."""
        self.graph_edge_controller.on_edge_removed(source_node, target_node)

    def update_stopping_nodes_display(self):
        """Update the stopping nodes list display."""
        self.node_sequence_controller.update_stopping_nodes_display()

    def add_selected_to_stopping_nodes(self):
        """Add selected nodes from canvas to stopping nodes list."""
        self.node_sequence_controller.add_selected_to_stopping_nodes()

    def remove_from_stopping_nodes(self):
        """Remove selected nodes from stopping nodes list."""
        self.node_sequence_controller.remove_from_stopping_nodes()

    def auto_detect_stopping_nodes(self):
        """Auto-detect stopping nodes (ContainerNodes / weights)."""
        self.node_sequence_controller.auto_detect_stopping_nodes()

    def mark_weights_processed(self):
        """Debug helper: mark all ContainerNodes as processed via the graph processor."""
        if (
            not self.graph
            or not hasattr(self, "graph_runner")
            or not self.graph_runner.graph_processor
        ):
            QMessageBox.warning(
                self, "No Graph/Processor", "Graph or processor not available."
            )
            return

        gp = self.graph_runner.graph_processor
        if hasattr(gp, "mark_container_nodes_as_processed"):
            count = gp.mark_container_nodes_as_processed()
            self.status_bar.showMessage(
                f"Marked {count} container nodes as processed (debug)"
            )
            # Force a visual update so dimming/active highlights reflect new status
            self.canvas.update_node_visuals(False, 0, 1)
            self.canvas.highlight_active_nodes(self.graph_runner.active_nodes)
        else:
            QMessageBox.information(
                self,
                "Not Supported",
                "Processor does not support marking container nodes as processed.",
            )

    def clear_stopping_nodes(self):
        """Clear all stopping nodes."""
        self.node_sequence_controller.clear_stopping_nodes()

    # --- Manual Sequence UI Handlers
    def add_selected_to_manual_sequence(self):
        """Add a step to the manual sequence using currently selected nodes on canvas."""
        self.node_sequence_controller.add_selected_to_manual_sequence()

    def add_selected_nodes_to_selected_step(self):
        """Append currently selected canvas nodes to the chosen manual sequence step."""
        self.node_sequence_controller.add_selected_nodes_to_selected_step()

    def replace_selected_step_with_selected_nodes(self):
        """Replace the chosen manual sequence step contents with the currently selected canvas nodes."""
        self.node_sequence_controller.replace_selected_step_with_selected_nodes()

    def remove_from_manual_sequence(self):
        """Remove selected step(s) from manual sequence UI and update graph property."""
        self.node_sequence_controller.remove_from_manual_sequence()

    def clear_manual_sequence(self):
        """Clear manual sequence from UI and graph property."""
        self.node_sequence_controller.clear_manual_sequence()

    def apply_manual_sequence_to_graph(self):
        """Take steps from UI list and set the graph manual_processing_sequence property accordingly."""
        self.node_sequence_controller.apply_manual_sequence_to_graph()

    def load_manual_sequence_from_graph(self):
        """Load the current graph.manual_processing_sequence into the UI list."""
        self.node_sequence_controller.load_manual_sequence_from_graph()

    def remove_from_starting_nodes(self):
        """Remove selected nodes from starting nodes list."""
        self.node_sequence_controller.remove_from_starting_nodes()

    def auto_detect_starting_nodes(self):
        """Auto-detect starting nodes (nodes with no predecessors)."""
        self.node_sequence_controller.auto_detect_starting_nodes()

    def clear_starting_nodes(self):
        """Clear all starting nodes."""
        self.node_sequence_controller.clear_starting_nodes()

    def on_processor_type_changed(self, index):
        """Handle processor type change. Delegated to ExecutionSettingsController."""
        self.execution_settings_controller.on_processor_type_changed(index)

    def on_threading_mode_changed(self, index):
        """Handle threading mode change. Delegated to ExecutionSettingsController."""
        self.execution_settings_controller.on_threading_mode_changed(index)

    # === Multi-Graph Support Methods ===

    def on_graph_selection_changed(self, index):
        """Handle graph selection change in the control panel dropdown."""
        if index == 0:
            # Mother Graph selected - process all nodes
            self.selected_processing_graph = None  # None means use mother graph
        else:
            # A sub-graph selected
            sub_graphs = getattr(self.graph, "sub_graphs", [])
            if index - 1 < len(sub_graphs):
                self.selected_processing_graph = sub_graphs[index - 1]
            else:
                self.selected_processing_graph = None

        # Update graph_runner to use the selected subgraph
        if hasattr(self, "graph_runner"):
            self.graph_runner.set_processing_subgraph(self.selected_processing_graph)

        # Update canvas to highlight selected graph
        if hasattr(self, "canvas"):
            self.canvas.refresh_subgraph_visuals()

    def update_graph_selector(self):
        """Update the graph selector dropdown with current sub-graphs."""
        if not hasattr(self, "graph_selector_combo"):
            return

        # Block signals to prevent spurious callbacks
        self.graph_selector_combo.blockSignals(True)

        # Clear and rebuild
        self.graph_selector_combo.clear()
        self.graph_selector_combo.addItem("Mother Graph (All)")

        # Add all sub-graphs
        if hasattr(self.graph, "sub_graphs"):
            for subgraph in self.graph.sub_graphs:
                name = getattr(subgraph, "graph_name", "Sub-Graph")
                color = getattr(subgraph, "graph_color", "#4ECDC4")
                # Add with colored icon indicator (using stylesheet)
                # Use ASCII dash prefix for portability instead of a bullet symbol
                self.graph_selector_combo.addItem(f"- {name}")
                # Set item color to match the sub-graph color
                idx = self.graph_selector_combo.count() - 1
                self.graph_selector_combo.setItemData(
                    idx, color, Qt.ItemDataRole.ForegroundRole
                )

        self.graph_selector_combo.blockSignals(False)

    def on_subgraph_created(self, subgraph):
        """Called when a new sub-graph is created."""
        self.update_graph_selector()
        # Log to console
        if hasattr(self, "console_controller"):
            self.console_controller.log(
                f"Sub-graph '{subgraph.graph_name}' created with {len(subgraph.nodes)} nodes."
            )

    def select_subgraph_nodes(self, subgraph):
        """Select all nodes belonging to a sub-graph on the canvas."""
        if hasattr(self, "canvas"):
            self.canvas.select_nodes_in_subgraph(subgraph)

    def choose_node_color(self):
        """Open color picker for node color."""
        self.visualization_controller.choose_node_color()

    def choose_text_color(self):
        """Open color picker for text color."""
        self.visualization_controller.choose_text_color()

    def apply_node_colors(self):
        """Apply selected colors to all nodes."""
        self.visualization_controller.apply_node_colors()

    def apply_node_colors_selected(self):
        """Apply selected colors only to currently selected node items on the canvas."""
        self.visualization_controller.apply_node_colors_selected()

    def open_plot_window(self):
        """Open the plot configuration dialog and create plot window."""
        self.plotting_controller.open_plot_window()

    def add_selected_to_plot(self):
        """Add currently selected node(s) in the canvas to the plot window."""
        self.plotting_controller.add_selected_to_plot()

    def _on_plot_backend_changed(self, index):
        """Handle plot backend change; if a plot is open with a different backend, recreate it."""
        self.plotting_controller.on_backend_changed(index)

    def _ensure_plot_backend_consistency(self):
        """If a plot window exists with a different backend than the selected dropdown, re-create it and preserve plotted nodes."""
        self.plotting_controller.ensure_backend_consistency()

    # Debug/dump_layout helper removed from GUI

    # apply_diagonal_layout removed from GUI; layout algorithms are no longer exposed via controls

    def _populate_examples_menu(self, menu):
        """Populate the examples menu with categories. Delegated to DialogController."""
        self.dialog_controller.populate_examples_menu(menu)

    def _load_example(self, builder, name: str):
        """Load an example graph. Delegated to DialogController."""
        self.dialog_controller.load_example(builder, name)

    def _show_mlp_dialog(self):
        """Show dialog to generate MLP graph. Delegated to DialogController."""
        self.dialog_controller.show_mlp_dialog()

    def _show_backprop_dialog(self):
        """Show dialog to add backpropagation to existing MLP. Delegated to DialogController."""
        self.dialog_controller.show_backprop_dialog()

    def _show_new_graph_dialog(self):
        """Show dialog to create a new graph. Delegated to DialogController."""
        self.dialog_controller.show_new_graph_dialog()

    def _visualize_graph_on_canvas(self, graph: Graph):
        """Visualize a graph object on the canvas. Delegated to GraphBuilderController."""
        self.graph_builder_controller.visualize_graph_on_canvas(graph)

    # Search functionality - delegated to SearchController

    def highlight_matching_nodes(self):
        """Highlight all nodes matching the search text."""
        self.search_controller.highlight_matching_nodes()

    def find_node(self):
        """Find and zoom to the first matching node."""
        self.search_controller.find_node()

    def find_next_node(self):
        """Find and zoom to the next matching node."""
        self.search_controller.find_next_node()

    def _focus_on_search_result(self):
        """Focus on the current search result."""
        self.search_controller._focus_on_search_result()

    # --- Layout methods - delegated to GraphLayoutController ---

    def _update_layout_status_label(self):
        """Update the layout status label. Delegated to GraphLayoutController."""
        self.graph_layout_controller.update_layout_status_label()

    def apply_graph_layout(self, layout_type: str, spacing: int = None):
        """Apply a graph layout algorithm. Delegated to GraphLayoutController."""
        self.graph_layout_controller.apply_graph_layout(layout_type, spacing)

    def _apply_layout_positions(self, positions: dict):
        """Apply layout positions. Delegated to GraphLayoutController."""
        self.graph_layout_controller._apply_layout_positions(positions)

    # --- Graph Simplification methods ---

    def simplify_step(self):
        """Apply one step of graph simplification."""
        if not self.graph or not self.graph.nodes:
            self.statusBar().showMessage("No graph to simplify", 3000)
            return

        # Import command for undo support
        from .commands.simplify_command import SimplifyStepCommand

        command = SimplifyStepCommand(self.canvas, self.graph)
        self.undo_stack.push(command)

        # Update status
        result = command.result
        if result and result.get("changed"):
            ops = result.get("operations", [])
            msg = (
                f"Simplify Step: {', '.join(ops)}"
                if ops
                else "Simplify Step: 1 operation applied"
            )
            self.statusBar().showMessage(msg, 5000)
        else:
            self.statusBar().showMessage("Simplify Step: No changes possible", 3000)

        self._update_simplification_status()

    def simplify_fully(self):
        """Fully simplify the graph structure."""
        if not self.graph or not self.graph.nodes:
            self.statusBar().showMessage("No graph to simplify", 3000)
            return

        # Import command for undo support
        from .commands.simplify_command import FullySimplifyCommand

        command = FullySimplifyCommand(self.canvas, self.graph)
        self.undo_stack.push(command)

        # Update status
        result = command.result
        if result:
            total = result.get("total_operations", 0)
            has_cycles = result.get("has_cycles", False)
            is_fully = result.get("is_fully_compressed", False)

            if total > 0:
                status = "fully simplified" if is_fully else "partially simplified"
                if has_cycles:
                    status += " (cycles detected)"
                msg = f"Fully Simplify: {total} operations, {status}"
            else:
                msg = "Fully Simplify: No changes possible"
            self.statusBar().showMessage(msg, 5000)
        else:
            self.statusBar().showMessage("Fully Simplify: Complete", 3000)

        self._update_simplification_status()

    def expand_step(self):
        """Expand the last simplified node (reverse simplification)."""
        if not self.graph or not self.graph.nodes:
            self.statusBar().showMessage("No graph to expand", 3000)
            return

        # Import command for undo support
        from .commands.simplify_command import ExpandStepCommand

        command = ExpandStepCommand(self.canvas, self.graph)
        self.undo_stack.push(command)

        # Update status
        result = command.result
        if result and result.get("expanded"):
            op = result.get("operation", "Expanded node")
            self.statusBar().showMessage(f"Expand Step: {op}", 5000)
        else:
            op = (
                result.get("operation", "No simplification history")
                if result
                else "Failed"
            )
            self.statusBar().showMessage(f"Expand Step: {op}", 3000)

        self._update_simplification_status()

    def _update_simplification_status(self):
        """Update the simplification status label."""
        if hasattr(self, "simplification_status_label") and self.graph:
            count = self.graph.get_simplification_history_count()
            self.simplification_status_label.setText(f"History: {count} operations")
