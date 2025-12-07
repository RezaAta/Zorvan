"""
Main window for the ComputationalGraphs visual editor.
"""

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
from .node_palette import NodePalette

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
        self.toggle_button.setStyleSheet(
            "QToolButton { text-align: left; padding: 6px 8px; border-radius: 6px; font-weight: bold; }"
            "QToolButton:checked { background-color: #239483; color: white; }"
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

        # Initial state
        self.content.setVisible(expanded)

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
        # Set a consistent application font for UI (adjustable)
        try:
            QApplication.setFont(QFont("Segoe UI", 10))
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
            print(f"Warning: Failed to initialize custom node manager: {e}")
            self.custom_node_manager = None

        # Core components
        # Create a new Graph object and use set_graph to keep everything in sync
        new_graph = Graph()
        self.graph_runner = GraphRunner(self)
        # Ensure runner and canvas reference the authoritative graph (use set_graph)
        try:
            self.set_graph(new_graph)
        except Exception:
            # If set_graph is not yet available, fallback to direct assignment
            self.graph = new_graph
            self.graph_runner.set_graph(self.graph)
        self.examples_loader = ExamplesLoader()

        # Connect signals
        self.graph_runner.step_completed.connect(self.on_step_completed)
        self.graph_runner.execution_finished.connect(self.on_execution_finished)
        self.graph_runner.error_occurred.connect(self.on_error)

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

        # State (must be before init_ui)
        self.colorize_enabled = False
        self.min_value_range = 0.0  # Numeric min value
        self.max_value_range = 1.0  # Numeric max value
        self.min_gradient_color = QColor(0, 0, 255)  # Blue for minimum
        self.max_gradient_color = QColor(255, 0, 0)  # Red for maximum
        self.skip_visualization = False  # Skip graph canvas updates
        self.skip_plotting = False  # Skip plot window updates
        self.saved_speed = 500  # For max speed toggle
        # ANN coloring state (checkbox)
        self.ann_colors_enabled = False

        # Plot window
        self.plot_window = None

        self.init_ui()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_status_bar()

    def set_graph(self, graph: Graph):
        """Set the authoritative Graph instance and keep canvas and runner in sync.

        This helps avoid stale references where UI actions affect a different graph
        object than the one used for processing.
        """
        self.graph = graph
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
        # Update displayed starting/stopping nodes
        try:
            self.update_starting_nodes_display()
            self.update_stopping_nodes_display()
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

        # Left dock - Node Palette
        self.palette = NodePalette(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.palette)

        # Right dock - Controls
        self.create_control_panel()
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

    def edit_node(self, node_item):
        """Open editor dialog for a specific node item. Delegated to NodeEditingController."""
        self.node_editing_controller.edit_node(node_item)

    def replace_node(self, node_item):
        """Replace node type. Delegated to NodeEditingController."""
        self.node_editing_controller.replace_node(node_item)

    def edit_selected_node(self):
        """Open editor for the selected node. Delegated to NodeEditingController."""
        self.node_editing_controller.edit_selected_node()

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
