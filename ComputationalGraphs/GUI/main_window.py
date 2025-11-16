"""
Main window for the ComputationalGraphs visual editor.
"""

from PyQt6.QtWidgets import (QMainWindow, QToolBar, QStatusBar, QDockWidget,
                             QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QLabel, QSlider, QSpinBox, QFileDialog, QMessageBox,
                             QCheckBox, QColorDialog, QComboBox, QScrollArea, QListWidget,
                             QDialog, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QColor, QBrush, QFont

from .graph_canvas import GraphCanvas
from .node_palette import NodePalette
from .node_editor_dialog import NodeEditorDialog
from .graph_runner import GraphRunner
from .examples_loader import ExamplesLoader
from .mlp_dialog import MLPGeneratorDialog
from .backprop_dialog import BackpropDialog
from .plot_window import PlotWindow, PlotConfigDialog

from ComputationalGraphs.Core.Graph import Graph


from PyQt6.QtWidgets import QToolButton, QSizePolicy


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
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        # Make header occupy the full horizontal width and style the active state
        self.toggle_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle_button.setStyleSheet(
            "QToolButton { text-align: left; padding: 6px 8px; border-radius: 6px; font-weight: bold; }"
            "QToolButton:checked { background-color: #239483; color: white; }"
        )
        # Ensure arrow and text align nicely and font weight is clear
        self.toggle_button.setFont(QFont(self.toggle_button.font().family(), self.toggle_button.font().pointSize(), QFont.Weight.Bold))
        # Use small arrow to indicate expand/collapse
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)

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
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)


class MainWindow(QMainWindow):
    """Main application window for the graph editor."""
    
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
        
        # Core components
        self.graph = Graph()
        self.graph_runner = GraphRunner(self)
        self.graph_runner.set_graph(self.graph)
        self.examples_loader = ExamplesLoader()
        
        # Connect signals
        self.graph_runner.step_completed.connect(self.on_step_completed)
        self.graph_runner.execution_finished.connect(self.on_execution_finished)
        self.graph_runner.error_occurred.connect(self.on_error)
        
        # State (must be before init_ui)
        self.colorize_enabled = False
        self.min_value_range = 0.0  # Numeric min value
        self.max_value_range = 1.0  # Numeric max value
        self.min_gradient_color = QColor(0, 0, 255)  # Blue for minimum
        self.max_gradient_color = QColor(255, 0, 0)  # Red for maximum
        self.skip_visualization = False  # Skip graph canvas updates
        self.skip_plotting = False  # Skip plot window updates
        self.saved_speed = 500  # For max speed toggle
        
        # Plot window
        self.plot_window = None
        
        self.init_ui()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_status_bar()
    
    def init_ui(self):
        """Initialize the UI components."""
        # Central widget - Graph Canvas
        self.canvas = GraphCanvas(self)
        self.canvas.edge_created.connect(self.on_edge_created)
        self.setCentralWidget(self.canvas)
        
        # Left dock - Node Palette
        self.palette = NodePalette(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.palette)
        
        # Right dock - Controls
        self.create_control_panel()
    
    def create_control_panel(self):
        """Create the control panel dock."""
        dock = QDockWidget("Controls", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)

        # Create a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Create section containers
        exec_container = QWidget()
        exec_layout = QVBoxLayout(exec_container)
        exec_layout.setContentsMargins(0, 0, 0, 0)

        viz_container = QWidget()
        viz_layout = QVBoxLayout(viz_container)
        viz_layout.setContentsMargins(0, 0, 0, 0)

        layout_container = QWidget()
        layout_layout = QVBoxLayout(layout_container)
        layout_layout.setContentsMargins(0, 0, 0, 0)

        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)

        # --- Execution controls (includes starting/stopping nodes for forward processing)
        exec_label = QLabel("<b>Execution Controls</b>")
        exec_layout.addWidget(exec_label)

        # Processor type selection
        processor_layout = QHBoxLayout()
        processor_layout.addWidget(QLabel("Processor:"))
        self.processor_combo = QComboBox()
        self.processor_combo.addItems(["Forward Processing", "Concurrent"])
        self.processor_combo.setCurrentIndex(1)  # Default to Concurrent
        self.processor_combo.currentIndexChanged.connect(self.on_processor_type_changed)
        processor_layout.addWidget(self.processor_combo)
        exec_layout.addLayout(processor_layout)

        # Threading mode selection (only for Concurrent mode)
        threading_layout = QHBoxLayout()
        threading_layout.addWidget(QLabel("Threading:"))
        self.threading_combo = QComboBox()
        self.threading_combo.addItems(["Single Thread", "Multi Thread"])
        self.threading_combo.setCurrentIndex(0)
        self.threading_combo.setEnabled(True)
        self.threading_combo.currentIndexChanged.connect(self.on_threading_mode_changed)
        threading_layout.addWidget(self.threading_combo)
        exec_layout.addLayout(threading_layout)

        # Starting nodes management (for Forward Processing)
        self.starting_nodes_widget = QWidget()
        self.starting_nodes_widget.setVisible(False)
        starting_nodes_group = QVBoxLayout(self.starting_nodes_widget)
        starting_nodes_group.setContentsMargins(0, 0, 0, 0)
        starting_nodes_label = QLabel("<b>Starting Nodes</b>")
        starting_nodes_group.addWidget(starting_nodes_label)

        # List widget to show starting nodes
        self.starting_nodes_list = QListWidget()
        self.starting_nodes_list.setMaximumHeight(120)
        self.starting_nodes_list.setStyleSheet("QListWidget { background-color: #2a2a2a; border: 1px solid #555; }")
        starting_nodes_group.addWidget(self.starting_nodes_list)

        # Buttons for managing starting nodes
        starting_nodes_btn_layout = QHBoxLayout()
        self.add_to_starting_btn = QPushButton("Add Selected")
        self.add_to_starting_btn.setToolTip("Add selected node(s) from canvas to starting nodes list")
        self.add_to_starting_btn.clicked.connect(self.add_selected_to_starting_nodes)
        starting_nodes_btn_layout.addWidget(self.add_to_starting_btn)

        self.remove_from_starting_btn = QPushButton("Remove")
        self.remove_from_starting_btn.setToolTip("Remove selected node(s) from starting nodes list")
        self.remove_from_starting_btn.clicked.connect(self.remove_from_starting_nodes)
        starting_nodes_btn_layout.addWidget(self.remove_from_starting_btn)
        starting_nodes_group.addLayout(starting_nodes_btn_layout)

        starting_nodes_btn_layout2 = QHBoxLayout()
        self.auto_detect_starting_btn = QPushButton("Auto-Detect")
        self.auto_detect_starting_btn.setToolTip("Auto-detect nodes with no predecessors")
        self.auto_detect_starting_btn.clicked.connect(self.auto_detect_starting_nodes)
        starting_nodes_btn_layout2.addWidget(self.auto_detect_starting_btn)

        self.clear_starting_btn = QPushButton("Clear All")
        self.clear_starting_btn.setToolTip("Clear all starting nodes")
        self.clear_starting_btn.clicked.connect(self.clear_starting_nodes)
        starting_nodes_btn_layout2.addWidget(self.clear_starting_btn)
        starting_nodes_group.addLayout(starting_nodes_btn_layout2)

        exec_layout.addWidget(self.starting_nodes_widget)

        # Stopping nodes management
        self.stopping_nodes_widget = QWidget()
        self.stopping_nodes_widget.setVisible(False)
        stopping_nodes_group = QVBoxLayout(self.stopping_nodes_widget)
        stopping_nodes_group.setContentsMargins(0, 0, 0, 0)
        stopping_nodes_label = QLabel("<b>Stopping Nodes</b>")
        stopping_nodes_group.addWidget(stopping_nodes_label)

        self.stopping_nodes_list = QListWidget()
        self.stopping_nodes_list.setMaximumHeight(120)
        self.stopping_nodes_list.setStyleSheet("QListWidget { background-color: #2a2a2a; border: 1px solid #555; }")
        stopping_nodes_group.addWidget(self.stopping_nodes_list)

        stopping_nodes_btn_layout = QHBoxLayout()
        self.add_to_stopping_btn = QPushButton("Add Selected")
        self.add_to_stopping_btn.setToolTip("Add selected node(s) from canvas to stopping nodes list")
        self.add_to_stopping_btn.clicked.connect(self.add_selected_to_stopping_nodes)
        stopping_nodes_btn_layout.addWidget(self.add_to_stopping_btn)

        self.remove_from_stopping_btn = QPushButton("Remove")
        self.remove_from_stopping_btn.setToolTip("Remove selected node(s) from stopping nodes list")
        self.remove_from_stopping_btn.clicked.connect(self.remove_from_stopping_nodes)
        stopping_nodes_btn_layout.addWidget(self.remove_from_stopping_btn)
        stopping_nodes_group.addLayout(stopping_nodes_btn_layout)

        stopping_nodes_btn_layout2 = QHBoxLayout()
        self.auto_detect_stopping_btn = QPushButton("Auto-Detect")
        self.auto_detect_stopping_btn.setToolTip("Auto-detect candidate stopping nodes (e.g., ContainerNodes)")
        self.auto_detect_stopping_btn.clicked.connect(self.auto_detect_stopping_nodes)
        stopping_nodes_btn_layout2.addWidget(self.auto_detect_stopping_btn)

        self.clear_stopping_btn = QPushButton("Clear All")
        self.clear_stopping_btn.setToolTip("Clear all stopping nodes")
        self.clear_stopping_btn.clicked.connect(self.clear_stopping_nodes)
        stopping_nodes_btn_layout2.addWidget(self.clear_stopping_btn)
        stopping_nodes_group.addLayout(stopping_nodes_btn_layout2)

        exec_layout.addWidget(self.stopping_nodes_widget)

        # Mark weights button (kept in Execution panel for visibility)
        self.mark_weights_processed_btn = QPushButton("Mark Weights Processed (Debug)")
        self.mark_weights_processed_btn.setToolTip("Mark all ContainerNode weights as processed (debug)")
        self.mark_weights_processed_btn.clicked.connect(self.mark_weights_processed)
        exec_layout.addWidget(self.mark_weights_processed_btn)

        exec_layout.addWidget(QLabel(""))  # Spacer

        # Play/Pause/Step/Reset and speed controls
        btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶ Start")
        self.play_btn.clicked.connect(self.play_graph)
        btn_layout.addWidget(self.play_btn)
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.pause_graph)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)
        exec_layout.addLayout(btn_layout)

        self.step_btn = QPushButton("Step →")
        self.step_btn.clicked.connect(self.step_graph)
        exec_layout.addWidget(self.step_btn)

        self.reset_btn = QPushButton("⏹ Reset")
        self.reset_btn.clicked.connect(self.reset_graph)
        exec_layout.addWidget(self.reset_btn)

        steps_layout = QHBoxLayout()
        steps_layout.addWidget(QLabel("Max Steps:"))
        self.max_steps_spin = QSpinBox()
        self.max_steps_spin.setRange(1, 10000)
        self.max_steps_spin.setValue(100)
        steps_layout.addWidget(self.max_steps_spin)
        exec_layout.addLayout(steps_layout)

        speed_layout = QVBoxLayout()
        self.max_speed_btn = QPushButton("⚡ Max Speed")
        self.max_speed_btn.setCheckable(True)
        self.max_speed_btn.setToolTip("Run at maximum speed (no delay between steps)")
        self.max_speed_btn.clicked.connect(self.on_max_speed_toggled)
        speed_layout.addWidget(self.max_speed_btn)

        self.skip_viz_check = QCheckBox("Skip Graph Visualization")
        self.skip_viz_check.setToolTip("Run all steps without updating graph visuals, then update at the end (faster)")
        self.skip_viz_check.stateChanged.connect(self.on_skip_viz_changed)
        speed_layout.addWidget(self.skip_viz_check)

        self.skip_plot_check = QCheckBox("Skip Plot Updates")
        self.skip_plot_check.setToolTip("Run without updating plot window during execution (faster)")
        self.skip_plot_check.stateChanged.connect(self.on_skip_plot_changed)
        speed_layout.addWidget(self.skip_plot_check)

        self.verbose_check = QCheckBox("Verbose Terminal Output")
        self.verbose_check.setToolTip("Enable detailed logging to terminal (may slow down execution)")
        self.verbose_check.stateChanged.connect(self.on_verbose_changed)
        speed_layout.addWidget(self.verbose_check)

        self.dim_processed_check = QCheckBox("Dim Processed Nodes (Debug)")
        self.dim_processed_check.setToolTip("Dim nodes that are marked 'processed' by the forward processor")
        self.dim_processed_check.stateChanged.connect(self.on_dim_processed_changed)
        speed_layout.addWidget(self.dim_processed_check)

        speed_layout.addWidget(QLabel("Speed (ms/step):"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 2000)
        self.speed_slider.setValue(500)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        speed_layout.addWidget(self.speed_slider)

        self.speed_label = QLabel("500 ms")
        speed_layout.addWidget(self.speed_label)
        exec_layout.addLayout(speed_layout)

        self.step_label = QLabel("Step: 0")
        exec_layout.addWidget(self.step_label)

        exec_layout.addWidget(QLabel(""))  # Spacer

        # --- Visualization controls
        viz_label = QLabel("<b>Visualization</b>")
        viz_layout.addWidget(viz_label)

        self.colorize_check = QCheckBox("Colorize by Value")
        self.colorize_check.stateChanged.connect(self.on_colorize_changed)
        viz_layout.addWidget(self.colorize_check)

        self.auto_range_btn = QPushButton("Auto Detect Min/Max")
        self.auto_range_btn.clicked.connect(self.auto_detect_range)
        self.auto_range_btn.setEnabled(False)
        viz_layout.addWidget(self.auto_range_btn)

        color_range_layout = QVBoxLayout()
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Min Value:"))
        self.min_value_label = QLabel("0.0")
        self.min_value_label.setStyleSheet("font-weight: bold;")
        min_layout.addWidget(self.min_value_label)
        min_layout.addStretch()
        color_range_layout.addLayout(min_layout)

        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max Value:"))
        self.max_value_label = QLabel("1.0")
        self.max_value_label.setStyleSheet("font-weight: bold;")
        max_layout.addWidget(self.max_value_label)
        max_layout.addStretch()
        color_range_layout.addLayout(max_layout)

        viz_layout.addLayout(color_range_layout)

        gradient_layout = QVBoxLayout()
        min_color_layout = QHBoxLayout()
        min_color_layout.addWidget(QLabel("Min Color:"))
        self.min_color_btn = QPushButton()
        self.min_color_btn.setFixedSize(60, 25)
        self.min_color_btn.setStyleSheet(f"background-color: {self.min_gradient_color.name()};")
        self.min_color_btn.clicked.connect(self.choose_min_color)
        min_color_layout.addWidget(self.min_color_btn)
        min_color_layout.addStretch()
        gradient_layout.addLayout(min_color_layout)

        max_color_layout = QHBoxLayout()
        max_color_layout.addWidget(QLabel("Max Color:"))
        self.max_color_btn = QPushButton()
        self.max_color_btn.setFixedSize(60, 25)
        self.max_color_btn.setStyleSheet(f"background-color: {self.max_gradient_color.name()};")
        self.max_color_btn.clicked.connect(self.choose_max_color)
        max_color_layout.addWidget(self.max_color_btn)
        max_color_layout.addStretch()
        gradient_layout.addLayout(max_color_layout)

        viz_layout.addLayout(gradient_layout)

        viz_layout.addWidget(QLabel(""))  # Spacer

        # Node appearance controls (moved to Visualization)
        appearance_label = QLabel("<b>Node Appearance</b>")
        viz_layout.addWidget(appearance_label)

        node_color_layout = QHBoxLayout()
        node_color_layout.addWidget(QLabel("Node Color:"))
        self.node_color_btn = QPushButton()
        self.node_color_btn.setFixedSize(60, 25)
        self.default_node_color = QColor(100, 150, 200)
        self.node_color_btn.setStyleSheet(f"background-color: {self.default_node_color.name()};")
        self.node_color_btn.clicked.connect(self.choose_node_color)
        node_color_layout.addWidget(self.node_color_btn)
        node_color_layout.addStretch()
        viz_layout.addLayout(node_color_layout)

        text_color_layout = QHBoxLayout()
        text_color_layout.addWidget(QLabel("Text Color:"))
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedSize(60, 25)
        self.default_text_color = QColor(255, 255, 255)
        self.text_color_btn.setStyleSheet(f"background-color: {self.default_text_color.name()};")
        self.text_color_btn.clicked.connect(self.choose_text_color)
        text_color_layout.addWidget(self.text_color_btn)
        text_color_layout.addStretch()
        viz_layout.addLayout(text_color_layout)

        self.apply_colors_btn = QPushButton("Apply to All Nodes")
        self.apply_colors_btn.clicked.connect(self.apply_node_colors)
        viz_layout.addWidget(self.apply_colors_btn)

        self.apply_selected_colors_btn = QPushButton("Apply to Selected")
        self.apply_selected_colors_btn.clicked.connect(self.apply_node_colors_selected)
        viz_layout.addWidget(self.apply_selected_colors_btn)

        # Move Apply ANN Colors to Visualization per request
        self.ann_colors_btn = QPushButton("Apply ANN Colors")
        self.ann_colors_btn.clicked.connect(self.canvas.apply_ann_colors)
        viz_layout.addWidget(self.ann_colors_btn)

        viz_layout.addStretch()

        # --- Layout controls
        layout_label = QLabel("<b>Layout</b>")
        layout_layout.addWidget(layout_label)

        self.spring_btn = QPushButton("Spring Layout")
        self.spring_btn.clicked.connect(lambda: self.canvas.apply_layout("spring"))
        layout_layout.addWidget(self.spring_btn)

        self.hierarchical_btn = QPushButton("Hierarchical Layout")
        self.hierarchical_btn.clicked.connect(lambda: self.canvas.apply_layout("hierarchical"))
        layout_layout.addWidget(self.hierarchical_btn)

        self.circular_btn = QPushButton("Circular Layout")
        self.circular_btn.clicked.connect(lambda: self.canvas.apply_layout("circular"))
        layout_layout.addWidget(self.circular_btn)

        self.ann_btn = QPushButton("ANN Layout (L→R)")
        self.ann_btn.clicked.connect(lambda: self.canvas.apply_layout("ann"))
        layout_layout.addWidget(self.ann_btn)

        layout_layout.addWidget(QLabel(""))  # Spacer

        # --- Plotting controls
        plotting_label = QLabel("<b>Plotting</b>")
        plot_layout.addWidget(plotting_label)

        self.open_plot_btn = QPushButton("📊 Open Plot Window")
        self.open_plot_btn.clicked.connect(self.open_plot_window)
        plot_layout.addWidget(self.open_plot_btn)

        self.add_to_plot_btn = QPushButton("➕ Add Selected to Plot")
        self.add_to_plot_btn.clicked.connect(self.add_selected_to_plot)
        plot_layout.addWidget(self.add_to_plot_btn)

        plot_layout.addStretch()

        # Add collapsible sections to main layout
        layout.addWidget(CollapsibleSection("Execution", exec_container, expanded=True))
        layout.addWidget(CollapsibleSection("Visualization", viz_container, expanded=True))
        layout.addWidget(CollapsibleSection("Layout", layout_container, expanded=False))
        layout.addWidget(CollapsibleSection("Plotting", plot_container, expanded=False))

        layout.addStretch()

        # Set the widget inside the scroll area
        scroll.setWidget(widget)
        dock.setWidget(scroll)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.control_dock = dock
    
    def create_actions(self):
        """Create menu actions."""
        # File actions
        self.new_action = QAction("&New", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self.new_graph)
        
        self.open_action = QAction("&Open...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_graph)
        
        self.save_action = QAction("&Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_graph)
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)
        
        # Edit actions
        self.delete_action = QAction("&Delete", self)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_action.triggered.connect(self.canvas.remove_selected_items)
        
        self.edit_node_action = QAction("&Edit Node...", self)
        self.edit_node_action.setShortcut(QKeySequence("Ctrl+E"))
        self.edit_node_action.triggered.connect(self.edit_selected_node)
    
    def create_menus(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        
        # Examples submenu
        examples_menu = file_menu.addMenu("&Examples")
        self._populate_examples_menu(examples_menu)
        
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self.delete_action)
        edit_menu.addAction(self.edit_node_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        mlp_action = QAction("Generate &MLP...", self)
        mlp_action.setShortcut(QKeySequence("Ctrl+M"))
        mlp_action.setStatusTip("Generate a new Multi-Layer Perceptron network")
        mlp_action.triggered.connect(self._show_mlp_dialog)
        tools_menu.addAction(mlp_action)
        
        backprop_action = QAction("Add &Backpropagation...", self)
        backprop_action.setShortcut(QKeySequence("Ctrl+B"))
        backprop_action.setStatusTip("Add backpropagation training to current MLP")
        backprop_action.triggered.connect(self._show_backprop_dialog)
        tools_menu.addAction(backprop_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        fit_view_action = QAction("&Fit All Nodes", self)
        fit_view_action.setShortcut(QKeySequence("F"))
        fit_view_action.setStatusTip("Fit all nodes in view (F)")
        fit_view_action.triggered.connect(self.canvas.fit_all_nodes_in_view)
        view_menu.addAction(fit_view_action)
        
        view_menu.addSeparator()
        view_menu.addAction(self.palette.toggleViewAction())
        view_menu.addAction(self.control_dock.toggleViewAction())
    
    def create_toolbars(self):
        """Create toolbars."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.delete_action)
        toolbar.addAction(self.edit_node_action)
        toolbar.addSeparator()
        
        # Add Find Node search bar
        from PyQt6.QtWidgets import QLineEdit
        toolbar.addWidget(QLabel("Find Node:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by node name...")
        self.search_box.setMaximumWidth(200)
        self.search_box.returnPressed.connect(self.find_node)
        self.search_box.textChanged.connect(self.highlight_matching_nodes)
        toolbar.addWidget(self.search_box)
        
        find_next_btn = QPushButton("Next")
        find_next_btn.clicked.connect(self.find_next_node)
        find_next_btn.setMaximumWidth(60)
        toolbar.addWidget(find_next_btn)
        
        # Track search results
        self.search_results = []
        self.search_index = -1
    
    def create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    # Graph operations
    
    def new_graph(self):
        """Create a new empty graph."""
        reply = QMessageBox.question(self, "New Graph",
                                     "Are you sure? Current graph will be lost.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.scene.clear()
            self.canvas.node_items.clear()
            self.canvas.edge_items.clear()
            
            self.graph = Graph()
            self.graph_runner.set_graph(self.graph)
            self.graph_runner.reset()
            
            self.status_bar.showMessage("New graph created")
    
    def open_graph(self):
        """Open a graph from file."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Graph", "",
                                                  "Python Files (*.py);;All Files (*)")
        
        if filename:
            # TODO: Implement graph loading
            self.status_bar.showMessage(f"Opening {filename}...")
            QMessageBox.information(self, "Not Implemented",
                                   "Graph loading not yet implemented.")
    
    def save_graph(self):
        """Save the current graph to file."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Graph", "",
                                                  "Python Files (*.py);;All Files (*)")
        
        if filename:
            # TODO: Implement graph saving
            self.status_bar.showMessage(f"Saving to {filename}...")
            QMessageBox.information(self, "Not Implemented",
                                   "Graph saving not yet implemented.")
    
    def edit_node(self, node_item):
        """Open editor dialog for a specific node item."""
        dialog = NodeEditorDialog(node_item.node, self)
        
        if dialog.exec():
            # Update visuals
            node_item.label.setPlainText(node_item.node.name)
            node_item.update_value_display()
            self.status_bar.showMessage(f"Node '{node_item.node.name}' updated")
    
    def edit_selected_node(self):
        """Open editor for the selected node."""
        selected = self.canvas.scene.selectedItems()
        
        from .node_item import NodeItem
        node_items = [item for item in selected if isinstance(item, NodeItem)]
        
        if not node_items:
            QMessageBox.information(self, "No Selection", "Please select a node to edit.")
            return
        
        node_item = node_items[0]
        self.edit_node(node_item)
    
    # Execution controls
    
    def play_graph(self):
        """Start graph execution."""
        # Rebuild graph from canvas
        self.rebuild_graph()
        
        max_steps = self.max_steps_spin.value()
        
        # Check if skip visualization (batch mode) is enabled
        if self.skip_visualization:
            self.run_batch_mode(max_steps)
        else:
            # Normal mode with visualization
            self.graph_runner.start(max_steps)
            
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.threading_combo.setEnabled(False)  # Disable threading mode while running
            self.status_bar.showMessage("Executing graph...")
    
    def run_batch_mode(self, max_steps):
        """Run all steps at once without updating visuals until complete."""
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.threading_combo.setEnabled(False)
        self.status_bar.showMessage(f"Batch mode: Running {max_steps} steps...")
        
        # Force UI update to show status
        QApplication.processEvents()
        
        try:
            # Run all steps without timer delays
            processor = self.graph_runner.graph_processor
            use_multithreading = self.graph_runner.use_multithreading
            processor_type = self.graph_runner.processor_type
            
            if processor_type == "forward":
                # Forward Processing
                starting_nodes = None
                if hasattr(self.graph, 'starting_nodes') and self.graph.starting_nodes:
                    starting_nodes = self.graph.starting_nodes
                processor.ForwardProcessing(iterations=max_steps, starting_nodes=starting_nodes)
            else:
                # Concurrent processing
                if use_multithreading:
                    processor.ComputeGraph(max_steps)
                else:
                    processor.ComputeGraphSingleThread(max_steps)
            
            # Update visuals once at the end
            self.step_label.setText(f"Step: {max_steps}")
            if self.colorize_enabled:
                self.auto_detect_range()
            else:
                self.canvas.update_node_visuals(False, 0, 1)
            
            # Update plot window if open (even if skip_plotting was enabled during execution)
            # In batch mode, we always update plot at the end
            if self.plot_window and self.plot_window.isVisible():
                self.plot_window.update_plot(max_steps)
            
            self.status_bar.showMessage(f"Batch mode complete: {max_steps} steps executed")
            
        except Exception as e:
            QMessageBox.critical(self, "Batch Execution Error", str(e))
            self.status_bar.showMessage("Batch execution failed")
        
        finally:
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.threading_combo.setEnabled(True)
    
    def pause_graph(self):
        """Pause graph execution."""
        self.graph_runner.pause()
        
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.threading_combo.setEnabled(True)  # Re-enable threading mode when paused
        self.status_bar.showMessage("Paused")
    
    def step_graph(self):
        """Execute a single step."""
        if not self.graph_runner.is_running:
            self.rebuild_graph()
        
        self.graph_runner.single_step()
    
    def reset_graph(self):
        """Reset graph execution."""
        self.graph_runner.reset()
        self.step_label.setText("Step: 0")
        
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.threading_combo.setEnabled(True)  # Re-enable threading mode selection
        
        # Reset visuals
        if self.colorize_enabled:
            self.auto_detect_range()
        else:
            self.canvas.update_node_visuals(False, 0, 1)
        
        self.status_bar.showMessage("Reset complete")
    
    def rebuild_graph(self):
        """Rebuild the graph from canvas nodes and edges."""
        # Preserve starting_nodes and stopping_nodes before rebuilding
        old_starting_nodes = list(self.graph.starting_nodes) if hasattr(self.graph, 'starting_nodes') else []
        old_stopping_nodes = list(self.graph.stopping_nodes) if hasattr(self.graph, 'stopping_nodes') else []
        
        self.graph = Graph()
        
        # Add all nodes
        for node in self.canvas.node_items.keys():
            self.graph.AddNode(node)
        
        # Add edges (connections)
        for edge_item in self.canvas.edge_items:
            source = edge_item.source_node.node
            target = edge_item.target_node.node
            
            # Add connection - check if source is not already a predecessor of target
            if source not in target.predecessors:
                target.AddPreNode(source)
        
        # Update adjacency matrix
        self.graph.UpdateAdjacencyMatrix()
        
        # Restore starting_nodes and stopping_nodes
        self.graph.starting_nodes = old_starting_nodes
        self.graph.stopping_nodes = old_stopping_nodes
        
        # Set the graph
        self.graph_runner.set_graph(self.graph)
    
    # Event handlers
    
    def on_step_completed(self, step):
        """Handle step completion."""
        self.step_label.setText(f"Step: {step}")
        
        # Skip visual updates if in batch mode (shouldn't be called in batch mode, but just in case)
        if self.skip_visualization:
            return
        
        # Update node visuals first (values and optionally colors)
        if self.colorize_enabled:
            self.auto_detect_range()
        else:
            self.canvas.update_node_visuals(False, 0, 1)
        
        # Highlight active nodes for Forward Processing
        # MUST be done AFTER colorization so it takes priority
        if self.graph_runner.processor_type == "forward":
            self.canvas.highlight_active_nodes(self.graph_runner.active_nodes)
            # Optionally dim nodes that the processor has marked as 'processed'
            # Use the checkbox state directly for robustness
            if self.dim_processed_check.isChecked():
                gp = getattr(self.graph_runner, 'graph_processor', None)
                if gp and hasattr(gp, '_node_status'):
                    processed_nodes = {n for n, s in gp._node_status.items() if s == 'processed'}
                    active_set = set(self.graph_runner.active_nodes)
                    for node, node_item in self.canvas.node_items.items():
                        # Active nodes stay fully bright
                        if node in active_set:
                            node_item.setOpacity(1.0)
                        elif node in processed_nodes:
                            node_item.setOpacity(0.25)
                        else:
                            node_item.setOpacity(1.0)
                        # Ensure visuals update immediately
                        try:
                            node_item.update()
                        except Exception:
                            pass
                else:
                    # If processor state unavailable, ensure full opacity
                    for node_item in self.canvas.node_items.values():
                        node_item.setOpacity(1.0)
                        try:
                            node_item.update()
                        except Exception:
                            pass
        else:
            # Clear active highlighting for concurrent mode
            self.canvas.highlight_active_nodes([])
        
        # Update plot window if open (unless skip_plotting is enabled)
        if not self.skip_plotting and self.plot_window and self.plot_window.isVisible():
            self.plot_window.update_plot(step)
    
    def on_execution_finished(self):
        """Handle execution completion."""
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.threading_combo.setEnabled(True)  # Re-enable threading mode when finished
        self.status_bar.showMessage("Execution finished")
    
    def on_error(self, message):
        """Handle execution error."""
        QMessageBox.critical(self, "Execution Error", message)
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.threading_combo.setEnabled(True)  # Re-enable threading mode on error
        self.status_bar.showMessage("Error occurred")
    
    def on_speed_changed(self, value):
        """Handle speed slider change."""
        self.speed_label.setText(f"{value} ms")
        self.graph_runner.set_speed(value)
    
    def on_max_speed_toggled(self, checked):
        """Handle max speed button toggle."""
        if checked:
            # Save current speed and set to minimum (10ms)
            self.saved_speed = self.speed_slider.value()
            self.speed_slider.setEnabled(False)
            self.graph_runner.set_speed(10)
            self.speed_label.setText("10 ms (MAX)")
            self.max_speed_btn.setText("⚡ Max Speed (ON)")
        else:
            # Restore previous speed
            self.speed_slider.setEnabled(True)
            if hasattr(self, 'saved_speed'):
                self.speed_slider.setValue(self.saved_speed)
                self.graph_runner.set_speed(self.saved_speed)
            self.max_speed_btn.setText("⚡ Max Speed")
    
    def on_skip_viz_changed(self, state):
        """Handle skip graph visualization checkbox change."""
        self.skip_visualization = (state == Qt.CheckState.Checked.value)
        
        if self.skip_visualization:
            # Disable speed controls when skipping graph updates
            self.speed_slider.setEnabled(False)
            self.max_speed_btn.setEnabled(False)
            self.status_bar.showMessage("Graph visualization skipped - will update at end")
        else:
            # Re-enable speed controls
            self.speed_slider.setEnabled(not self.max_speed_btn.isChecked())
            self.max_speed_btn.setEnabled(True)
            self.status_bar.showMessage("Graph visualization enabled")
    
    def on_skip_plot_changed(self, state):
        """Handle skip plot updates checkbox change."""
        self.skip_plotting = (state == Qt.CheckState.Checked.value)
        
        if self.skip_plotting:
            self.status_bar.showMessage("Plot updates skipped - will update at end")
        else:
            self.status_bar.showMessage("Plot updates enabled")
    
    def on_verbose_changed(self, state):
        """Handle verbose checkbox change."""
        verbose_enabled = (state == Qt.CheckState.Checked.value)
        
        # Update the graph processor's verbose flag
        if self.graph_runner and self.graph_runner.graph_processor:
            self.graph_runner.graph_processor.verbose = verbose_enabled
            
            if verbose_enabled:
                self.status_bar.showMessage("Verbose output enabled - check terminal")
            else:
                self.status_bar.showMessage("Verbose output disabled")

    def on_dim_processed_changed(self, state):
        """Handle dim-processed checkbox change."""
        # Use the checkbox directly elsewhere; but keep a convenience attribute
        self.dim_processed_enabled = (state == Qt.CheckState.Checked.value)
        # Reset opacities when toggled off
        if not self.dim_processed_check.isChecked():
            for node_item in self.canvas.node_items.values():
                node_item.setOpacity(1.0)
                try:
                    node_item.update()
                except Exception:
                    pass
        self.status_bar.showMessage("Dim processed nodes: " + ("ON" if self.dim_processed_check.isChecked() else "OFF"))
    
    def on_colorize_changed(self, state):
        """Handle colorize checkbox change."""
        self.colorize_enabled = (state == Qt.CheckState.Checked.value)
        self.auto_range_btn.setEnabled(self.colorize_enabled)
        
        if self.colorize_enabled:
            # Auto detect min/max on first enable
            self.auto_detect_range()
        else:
            self.canvas.update_node_visuals(False, 0, 1)
    
    def auto_detect_range(self):
        """Automatically detect min and max values from current node values."""
        if not self.canvas.node_items:
            self.status_bar.showMessage("No nodes to analyze")
            return
        
        # Collect all numeric values
        values = []
        for node_item in self.canvas.node_items.values():
            value = node_item.node.value
            if isinstance(value, (int, float)):
                values.append(value)
        
        if not values:
            self.status_bar.showMessage("No numeric values found")
            return
        
        # Set min and max numeric values
        self.min_value_range = min(values)
        self.max_value_range = max(values)
        
        # Update labels
        self.min_value_label.setText(f"{self.min_value_range:.2f}")
        self.max_value_label.setText(f"{self.max_value_range:.2f}")
        
        # Update visuals with numeric range and color gradient
        if self.colorize_enabled:
            self.canvas.update_node_visuals(
                True, 
                self.min_value_range, 
                self.max_value_range,
                self.min_gradient_color,
                self.max_gradient_color
            )
        
        self.status_bar.showMessage(f"Auto detected range: {self.min_value_range:.2f} to {self.max_value_range:.2f}")
    
    def choose_min_color(self):
        """Choose color for minimum values."""
        color = QColorDialog.getColor(self.min_gradient_color, self, "Choose Min Value Color")
        if color.isValid():
            self.min_gradient_color = color
            self.min_color_btn.setStyleSheet(f"background-color: {color.name()};")
            if self.colorize_enabled:
                self.canvas.update_node_visuals(
                    True,
                    self.min_value_range,
                    self.max_value_range,
                    self.min_gradient_color,
                    self.max_gradient_color
                )
    
    def choose_max_color(self):
        """Choose color for maximum values."""
        color = QColorDialog.getColor(self.max_gradient_color, self, "Choose Max Value Color")
        if color.isValid():
            self.max_gradient_color = color
            self.max_color_btn.setStyleSheet(f"background-color: {color.name()};")
            if self.colorize_enabled:
                self.canvas.update_node_visuals(
                    True,
                    self.min_value_range,
                    self.max_value_range,
                    self.min_gradient_color,
                    self.max_gradient_color
                )
    
    def on_edge_created(self, source_node, target_node):
        """Handle edge creation."""
        self.status_bar.showMessage(f"Connected {source_node.name} → {target_node.name}")
    
    def update_starting_nodes_display(self):
        """Update the starting nodes list display."""
        self.starting_nodes_list.clear()
        
        if not self.graph:
            return
        
        # Check if graph has starting_nodes attribute
        if hasattr(self.graph, 'starting_nodes') and self.graph.starting_nodes:
            for node in self.graph.starting_nodes:
                self.starting_nodes_list.addItem(node.name)
        else:
            # Auto-detect nodes with no predecessors and show in gray (not set)
            source_nodes = [node for node in self.graph.nodes if len(node.predecessors) == 0]
            for node in source_nodes:
                item_text = f"(auto) {node.name}"
                self.starting_nodes_list.addItem(item_text)
    
    def add_selected_to_starting_nodes(self):
        """Add selected nodes from canvas to starting nodes list."""
        if not self.graph:
            QMessageBox.warning(self, "No Graph", "Please load a graph first.")
            return
        
        # Get selected nodes from canvas
        selected_items = [item for item in self.canvas.scene.selectedItems() 
                         if hasattr(item, 'node')]
        
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select node(s) on the canvas first.")
            return
        
        # Initialize starting_nodes if not exists
        if not hasattr(self.graph, 'starting_nodes') or self.graph.starting_nodes is None:
            self.graph.starting_nodes = []
        
        # Add selected nodes to starting_nodes (avoid duplicates)
        added_count = 0
        for item in selected_items:
            if item.node not in self.graph.starting_nodes:
                self.graph.starting_nodes.append(item.node)
                added_count += 1
        
        self.update_starting_nodes_display()
        self.status_bar.showMessage(f"Added {added_count} node(s) to starting nodes")

    def update_stopping_nodes_display(self):
        """Update the stopping nodes list display."""
        self.stopping_nodes_list.clear()

        if not self.graph:
            return

        if hasattr(self.graph, 'stopping_nodes') and self.graph.stopping_nodes:
            for node in self.graph.stopping_nodes:
                self.stopping_nodes_list.addItem(node.name)

    def add_selected_to_stopping_nodes(self):
        """Add selected nodes from canvas to stopping nodes list."""
        if not self.graph:
            QMessageBox.warning(self, "No Graph", "Please load a graph first.")
            return

        selected_items = [item for item in self.canvas.scene.selectedItems() 
                         if hasattr(item, 'node')]

        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select node(s) on the canvas first.")
            return

        if not hasattr(self.graph, 'stopping_nodes') or self.graph.stopping_nodes is None:
            self.graph.stopping_nodes = []

        added_count = 0
        for item in selected_items:
            if item.node not in self.graph.stopping_nodes:
                self.graph.stopping_nodes.append(item.node)
                added_count += 1

        self.update_stopping_nodes_display()
        self.status_bar.showMessage(f"Added {added_count} node(s) to stopping nodes")

    def remove_from_stopping_nodes(self):
        """Remove selected nodes from stopping nodes list."""
        if not self.graph or not hasattr(self.graph, 'stopping_nodes') or not self.graph.stopping_nodes:
            return

        selected_items = self.stopping_nodes_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select node(s) from the stopping nodes list.")
            return

        removed_count = 0
        for item in selected_items:
            node_name = item.text()
            for node in self.graph.stopping_nodes[:]:
                if node.name == node_name:
                    self.graph.stopping_nodes.remove(node)
                    removed_count += 1
                    break

        self.update_stopping_nodes_display()
        self.status_bar.showMessage(f"Removed {removed_count} node(s) from stopping nodes")

    def auto_detect_stopping_nodes(self):
        """Auto-detect stopping nodes (ContainerNodes / weights)."""
        if not self.graph:
            QMessageBox.warning(self, "No Graph", "Please load a graph first.")
            return

        from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
        candidates = [n for n in self.graph.nodes if isinstance(n, ContainerNode)]

        if not candidates:
            QMessageBox.warning(self, "No Candidates", "No ContainerNode candidates found.")
            return

        self.graph.stopping_nodes = candidates
        self.update_stopping_nodes_display()
        self.status_bar.showMessage(f"Auto-detected {len(candidates)} stopping node(s)")

    def mark_weights_processed(self):
        """Debug helper: mark all ContainerNodes as processed via the graph processor."""
        if not self.graph or not hasattr(self, 'graph_runner') or not self.graph_runner.graph_processor:
            QMessageBox.warning(self, "No Graph/Processor", "Graph or processor not available.")
            return

        gp = self.graph_runner.graph_processor
        if hasattr(gp, 'mark_container_nodes_as_processed'):
            count = gp.mark_container_nodes_as_processed()
            self.status_bar.showMessage(f"Marked {count} container nodes as processed (debug)")
            # Force a visual update so dimming/active highlights reflect new status
            self.canvas.update_node_visuals(False, 0, 1)
            self.canvas.highlight_active_nodes(self.graph_runner.active_nodes)
        else:
            QMessageBox.information(self, "Not Supported", "Processor does not support marking container nodes as processed.")

    def clear_stopping_nodes(self):
        """Clear all stopping nodes."""
        if not self.graph:
            return

        if hasattr(self.graph, 'stopping_nodes'):
            self.graph.stopping_nodes = []

        self.update_stopping_nodes_display()
        self.status_bar.showMessage("Cleared all stopping nodes")
    
    def remove_from_starting_nodes(self):
        """Remove selected nodes from starting nodes list."""
        if not self.graph or not hasattr(self.graph, 'starting_nodes') or not self.graph.starting_nodes:
            return
        
        # Get selected items from the list
        selected_items = self.starting_nodes_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select node(s) from the starting nodes list.")
            return
        
        # Remove nodes by name
        removed_count = 0
        for item in selected_items:
            node_name = item.text().replace("(auto) ", "")  # Remove auto prefix if present
            # Find and remove the node
            for node in self.graph.starting_nodes[:]:  # Use slice to modify while iterating
                if node.name == node_name:
                    self.graph.starting_nodes.remove(node)
                    removed_count += 1
                    break
        
        self.update_starting_nodes_display()
        self.status_bar.showMessage(f"Removed {removed_count} node(s) from starting nodes")
    
    def auto_detect_starting_nodes(self):
        """Auto-detect starting nodes (nodes with no predecessors)."""
        if not self.graph:
            QMessageBox.warning(self, "No Graph", "Please load a graph first.")
            return
        
        # Find nodes with no predecessors
        source_nodes = [node for node in self.graph.nodes if len(node.predecessors) == 0]
        
        if not source_nodes:
            QMessageBox.warning(self, "No Sources Found", 
                              "No nodes with zero predecessors found.\nGraph may have cycles or all nodes have inputs.")
            return
        
        # Set as starting nodes
        self.graph.starting_nodes = source_nodes
        self.update_starting_nodes_display()
        self.status_bar.showMessage(f"Auto-detected {len(source_nodes)} starting node(s)")
    
    def clear_starting_nodes(self):
        """Clear all starting nodes."""
        if not self.graph:
            return
        
        if hasattr(self.graph, 'starting_nodes'):
            self.graph.starting_nodes = []
        
        self.update_starting_nodes_display()
        self.status_bar.showMessage("Cleared all starting nodes")
    
    def on_processor_type_changed(self, index):
        """Handle processor type selection change."""
        processor_type = "forward" if index == 0 else "concurrent"
        self.graph_runner.set_processor_type(processor_type)
        
        # Show/hide forward processing panels based on mode
        is_forward_mode = (index == 0)
        self.starting_nodes_widget.setVisible(is_forward_mode)
        self.stopping_nodes_widget.setVisible(is_forward_mode)
        
        # Disable threading combo for Forward Processing (not applicable)
        # Threading only applies to Concurrent mode
        self.threading_combo.setEnabled(index == 1)
        
        type_name = "Forward Processing" if index == 0 else "Concurrent"
        self.status_bar.showMessage(f"Processor type: {type_name}")
        
        # Update starting nodes display when switching to Forward Processing
        if index == 0:
            self.update_starting_nodes_display()
            self.update_stopping_nodes_display()
    
    def on_threading_mode_changed(self, index):
        """Handle threading mode selection change."""
        use_multithreading = (index == 1)  # 0 = Single Thread, 1 = Multi Thread
        self.graph_runner.set_threading_mode(use_multithreading)
        mode_name = "Multi-threaded" if use_multithreading else "Single-threaded"
        self.status_bar.showMessage(f"Processing mode: {mode_name}")
    
    def choose_node_color(self):
        """Open color picker for node color."""
        color = QColorDialog.getColor(self.default_node_color, self, "Choose Node Color")
        if color.isValid():
            self.default_node_color = color
            self.node_color_btn.setStyleSheet(f"background-color: {color.name()};")
    
    def choose_text_color(self):
        """Open color picker for text color."""
        color = QColorDialog.getColor(self.default_text_color, self, "Choose Text Color")
        if color.isValid():
            self.default_text_color = color
            self.text_color_btn.setStyleSheet(f"background-color: {color.name()};")
    
    def apply_node_colors(self):
        """Apply selected colors to all nodes."""
        for node_item in self.canvas.node_items.values():
            # Update node fill color
            node_item.default_color = self.default_node_color
            node_item.setBrush(QBrush(self.default_node_color))
            
            # Update text color
            node_item.label.setDefaultTextColor(self.default_text_color)
            node_item.value_label.setDefaultTextColor(self.default_text_color)
            
            # Trigger repaint
            node_item.update()
        
        self.status_bar.showMessage(f"Applied colors to {len(self.canvas.node_items)} nodes")

    def apply_node_colors_selected(self):
        """Apply selected colors only to currently selected node items on the canvas."""
        from .node_item import NodeItem

        selected_items = self.canvas.scene.selectedItems()
        node_items = [item for item in selected_items if isinstance(item, NodeItem)]

        if not node_items:
            QMessageBox.information(self, "No Selection", "Please select node(s) on the canvas first.")
            return

        for node_item in node_items:
            node_item.default_color = self.default_node_color
            node_item.setBrush(QBrush(self.default_node_color))
            node_item.label.setDefaultTextColor(self.default_text_color)
            node_item.value_label.setDefaultTextColor(self.default_text_color)
            node_item.update()

        self.status_bar.showMessage(f"Applied colors to {len(node_items)} selected node(s)")
    
    def open_plot_window(self):
        """Open the plot configuration dialog and create plot window."""
        if not self.graph or len(self.graph.nodes) == 0:
            QMessageBox.warning(self, "No Graph", "Please load or create a graph first.")
            return
        
        # Get max iterations from the control panel
        default_max_iter = self.max_steps_spin.value()
        
        # Open configuration dialog
        config_dialog = PlotConfigDialog(self.graph, default_max_iter, self)
        if config_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_nodes = config_dialog.get_selected_nodes()
            
            if not selected_nodes:
                QMessageBox.warning(self, "No Nodes Selected", 
                                  "Please select at least one node to plot.")
                return
            
            max_iterations = config_dialog.get_max_iterations()
            
            # Close existing plot window if any
            if self.plot_window:
                self.plot_window.close()
            
            # Create new plot window as standalone (no parent)
            self.plot_window = PlotWindow(selected_nodes, max_iterations, None)
            self.plot_window.setWindowTitle("Node Values Plot - Computational Graphs")
            self.plot_window.show()
            
            # Update plot with current iteration (if graph is running)
            if hasattr(self.graph_runner, '_iteration_counter'):
                self.plot_window.update_plot(self.graph_runner._iteration_counter)
            
            self.status_bar.showMessage(f"Plotting {len(selected_nodes)} nodes")
    
    def add_selected_to_plot(self):
        """Add currently selected node(s) in the canvas to the plot window."""
        selected_items = self.canvas.scene.selectedItems()
        
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                   "Please select a node in the canvas first.")
            return
        
        # Filter for node items only
        from .node_item import NodeItem
        node_items = [item for item in selected_items if isinstance(item, NodeItem)]
        
        if not node_items:
            QMessageBox.information(self, "No Nodes Selected", 
                                   "Please select a node (not an edge).")
            return
        
        # Create plot window if it doesn't exist
        if not self.plot_window or not self.plot_window.isVisible():
            # Create with first selected node as standalone window
            max_iterations = self.max_steps_spin.value()
            first_node = node_items[0].node
            self.plot_window = PlotWindow([first_node], max_iterations, None)
            self.plot_window.setWindowTitle("Node Values Plot - Computational Graphs")
            self.plot_window.show()
            node_items = node_items[1:]  # Remove first node since it's already added
        
        # Add remaining selected nodes to plot
        for node_item in node_items:
            self.plot_window.add_node(node_item.node)
        
        node_count = len([item for item in selected_items if isinstance(item, NodeItem)])
        self.status_bar.showMessage(f"Added {node_count} node(s) to plot")
    
    def _populate_examples_menu(self, menu):
        """Populate the examples menu with categories."""
        from PyQt6.QtGui import QAction
        
        for category in self.examples_loader.get_categories():
            category_menu = menu.addMenu(category.name)
            category_menu.setToolTip(category.description)
            
            for name, description, builder in category.examples:
                action = QAction(name, self)
                action.setStatusTip(description)
                action.triggered.connect(lambda checked, b=builder, n=name: self._load_example(b, n))
                category_menu.addAction(action)
    
    def _load_example(self, builder, name: str):
        """Load an example graph."""
        try:
            # Build the example graph
            example_graph = builder()
            
            # Clear current canvas
            self.canvas.scene.clear()
            self.canvas.node_items.clear()
            self.canvas.edge_items.clear()
            
            # Load the new graph
            self.graph = example_graph
            self.graph_runner.set_graph(self.graph)
            
            # DON'T reset when loading - it clears DataStreamNode data!
            # self.graph_runner.reset()
            
            # Visualize the graph on canvas
            self._visualize_graph_on_canvas(example_graph)
            
            # Update starting nodes display
            self.update_starting_nodes_display()
            self.update_stopping_nodes_display()
            
            # No need to apply layout separately - already done in _visualize_graph_on_canvas
            
            self.status_bar.showMessage(f"Loaded example: {name}")
            
        except Exception as e:
            import traceback
            full_error = traceback.format_exc()
            print(f"\n{'='*60}")
            print(f"ERROR loading example '{name}':")
            print(full_error)
            print(f"{'='*60}\n")
            QMessageBox.critical(
                self,
                "Error Loading Example",
                f"Failed to load example '{name}':\n{str(e)}\n\nSee console for full traceback."
            )
    
    def _show_mlp_dialog(self):
        """Show dialog to generate MLP graph."""
        dialog = MLPGeneratorDialog(self)
        if dialog.exec():
            generated_graph = dialog.get_graph()
            
            # Clear current canvas
            self.canvas.scene.clear()
            self.canvas.node_items.clear()
            self.canvas.edge_items.clear()
            
            # Load the generated graph
            self.graph = generated_graph
            self.graph_runner.set_graph(self.graph)
            # DON'T reset when loading - it clears DataStreamNode data!
            # self.graph_runner.reset()
            
            # Visualize the graph on canvas
            self._visualize_graph_on_canvas(generated_graph)
            self.update_stopping_nodes_display()
            self.status_bar.showMessage("MLP generated successfully")
    
    def _show_backprop_dialog(self):
        """Show dialog to add backpropagation to existing MLP."""
        if not self.graph or len(self.graph.nodes) == 0:
            QMessageBox.warning(
                self,
                "No Graph",
                "Please load or create a graph first."
            )
            return
        
        dialog = BackpropDialog(self.graph, self)
        if dialog.exec():
            generated_graph = dialog.get_graph()
            
            # Clear current canvas
            self.canvas.scene.clear()
            self.canvas.node_items.clear()
            self.canvas.edge_items.clear()
            
            # Load the graph with backprop
            self.graph = generated_graph
            self.graph_runner.set_graph(self.graph)
            # DON'T reset when loading - it clears DataStreamNode data!
            # self.graph_runner.reset()
            
            # Visualize the graph on canvas
            self._visualize_graph_on_canvas(generated_graph)
            self.update_stopping_nodes_display()
            
            self.status_bar.showMessage("Backpropagation added successfully")
    
    def _visualize_graph_on_canvas(self, graph: Graph):
        """Visualize a graph object on the canvas."""
        try:
            # Import node_item here to avoid circular import
            from .node_item import NodeItem
            from .edge_item import EdgeItem
            import networkx as nx
            
            # Create a networkx graph for layout
            G = nx.DiGraph()
            
            # Add nodes to networkx graph
            for node in graph.nodes:
                G.add_node(node)
            
            # Add edges based on predecessors
            for node in graph.nodes:
                if hasattr(node, 'predecessors') and node.predecessors:
                    for pred in node.predecessors:
                        G.add_edge(pred, node)
            
            # Compute layout with ANN method (better spacing and works for all graphs)
            num_nodes = len(G.nodes())
            base_scale = 300
            scale = base_scale * max(1.0, num_nodes / 15)
            
            # Use ANN layout directly - it's the best for all graph types
            pos = self.canvas._compute_ann_layout(G, scale)
            
            # No offset needed, center at origin
            offset_x = 0
            offset_y = 0
            
            # Create node items with collision avoidance
            min_distance = 100  # Minimum distance between nodes
            created_positions = {}  # Track created node positions
            
            for node in graph.nodes:
                node_pos = pos.get(node, (0, 0))
                x = node_pos[0] + offset_x
                y = node_pos[1] + offset_y
                
                # Check for collisions and adjust position
                adjusted_x, adjusted_y = x, y
                max_attempts = 50
                
                for attempt in range(max_attempts):
                    collision = False
                    for other_pos in created_positions.values():
                        dx = adjusted_x - other_pos[0]
                        dy = adjusted_y - other_pos[1]
                        distance = (dx**2 + dy**2)**0.5
                        
                        if distance < min_distance:
                            collision = True
                            # Push away from collision
                            if distance > 0:
                                push_x = (dx / distance) * (min_distance - distance)
                                push_y = (dy / distance) * (min_distance - distance)
                                adjusted_x += push_x * 0.5
                                adjusted_y += push_y * 0.5
                            else:
                                # If exactly overlapping, add random offset
                                import random
                                adjusted_x += random.uniform(-50, 50)
                                adjusted_y += random.uniform(-50, 50)
                    
                    if not collision:
                        break
                
                # Store position and create node
                created_positions[node] = (adjusted_x, adjusted_y)
                node_item = NodeItem(node, adjusted_x, adjusted_y)
                self.canvas.scene.addItem(node_item)
                self.canvas.node_items[node] = node_item
            
            # Create edge items
            for node in graph.nodes:
                if hasattr(node, 'predecessors') and node.predecessors:
                    target_item = self.canvas.node_items.get(node)
                    if target_item:
                        for pred in node.predecessors:
                            source_item = self.canvas.node_items.get(pred)
                            if source_item:
                                edge = EdgeItem(source_item, target_item)
                                self.canvas.scene.addItem(edge)
                                self.canvas.edge_items.append(edge)
                                source_item.add_edge(edge)
                                target_item.add_edge(edge)
            
            # Update visuals
            if self.colorize_enabled:
                self.auto_detect_range()
            else:
                self.canvas.update_node_visuals(False, 0, 1)
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Visualization Error",
                f"Graph loaded but visualization failed:\n{str(e)}\n\n"
                "You can still run the graph, but the visual layout may not be optimal."
            )
    
    def highlight_matching_nodes(self):
        """Highlight all nodes matching the search text."""
        search_text = self.search_box.text().strip().lower()
        
        if not search_text:
            # Clear all highlights
            for node_item in self.canvas.node_items.values():
                node_item.setOpacity(1.0)
                pen = node_item.pen()
                pen.setWidth(2)
                pen.setColor(QColor(100, 100, 100))
                node_item.setPen(pen)
            return
        
        # Dim all nodes first
        for node_item in self.canvas.node_items.values():
            node_item.setOpacity(0.3)
        
        # Find and highlight matching nodes
        self.search_results = []
        for node_item in self.canvas.node_items.values():
            if search_text in node_item.node.name.lower():
                node_item.setOpacity(1.0)
                # Add yellow highlight
                pen = node_item.pen()
                pen.setWidth(4)
                pen.setColor(QColor(255, 255, 0))
                node_item.setPen(pen)
                self.search_results.append(node_item)
        
        self.search_index = -1
        
        # Update status
        if self.search_results:
            self.status_bar.showMessage(f"Found {len(self.search_results)} node(s) matching '{search_text}'")
        else:
            self.status_bar.showMessage(f"No nodes found matching '{search_text}'")
    
    def find_node(self):
        """Find and zoom to the first matching node."""
        if self.search_results:
            self.search_index = 0
            self._focus_on_search_result()
    
    def find_next_node(self):
        """Find and zoom to the next matching node."""
        if not self.search_results:
            self.status_bar.showMessage("No search results. Enter text in the search box.")
            return
        
        self.search_index = (self.search_index + 1) % len(self.search_results)
        self._focus_on_search_result()
    
    def _focus_on_search_result(self):
        """Focus on the current search result."""
        if not self.search_results or self.search_index < 0:
            return
        
        node_item = self.search_results[self.search_index]
        
        # Update all highlights
        for item in self.search_results:
            pen = item.pen()
            pen.setWidth(4)
            pen.setColor(QColor(255, 255, 0))
            item.setPen(pen)
        
        # Highlight current with green
        pen = node_item.pen()
        pen.setWidth(6)
        pen.setColor(QColor(0, 255, 0))
        node_item.setPen(pen)
        
        # Center view on node
        self.canvas.centerOn(node_item)
        
        # Update status
        self.status_bar.showMessage(
            f"Node {self.search_index + 1} of {len(self.search_results)}: {node_item.node.name}"
        )
