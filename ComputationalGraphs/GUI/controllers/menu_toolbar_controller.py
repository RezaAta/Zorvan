"""
MenuToolbarController - Manages menu bar, actions, and toolbars.

Extracted from MainWindow as part of Clean Code refactoring.
Handles creation of actions, menus, toolbars, and status bar.
"""

from typing import TYPE_CHECKING

from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QStatusBar, QToolBar

if TYPE_CHECKING:
    from ..main_window import MainWindow


class MenuToolbarController:
    """Controller for menu bar, actions, and toolbars."""

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window

    def create_actions(self):
        """Create menu actions."""
        mw = self.main_window

        # File actions
        mw.new_action = QAction("&New", mw)
        mw.new_action.setShortcut(QKeySequence.StandardKey.New)
        mw.new_action.triggered.connect(mw.new_graph)

        mw.open_action = QAction("&Open...", mw)
        mw.open_action.setShortcut(QKeySequence.StandardKey.Open)
        mw.open_action.triggered.connect(mw.open_graph)

        mw.save_action = QAction("&Save", mw)
        mw.save_action.setShortcut(QKeySequence.StandardKey.Save)
        mw.save_action.triggered.connect(mw.save_graph)

        mw.exit_action = QAction("E&xit", mw)
        mw.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        mw.exit_action.triggered.connect(mw.close)

        # Undo / Redo actions
        mw.undo_action = QAction("&Undo", mw)
        mw.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        mw.undo_action.triggered.connect(mw.undo_stack.undo)
        mw.undo_stack.canUndoChanged.connect(mw.undo_action.setEnabled)
        mw.undo_action.setEnabled(mw.undo_stack.canUndo())

        mw.redo_action = QAction("&Redo", mw)
        mw.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        mw.redo_action.triggered.connect(mw.undo_stack.redo)
        mw.undo_stack.canRedoChanged.connect(mw.redo_action.setEnabled)
        mw.redo_action.setEnabled(mw.undo_stack.canRedo())

        # Edit actions
        mw.delete_action = QAction("&Delete", mw)
        mw.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        mw.delete_action.triggered.connect(mw.canvas.delete_selected_with_undo)

        mw.swallow_action = QAction("&Swallow Node", mw)
        mw.swallow_action.setShortcut(QKeySequence("Ctrl+Delete"))
        mw.swallow_action.setStatusTip(
            "Remove selected nodes while connecting predecessors to successors"
        )
        mw.swallow_action.triggered.connect(mw.canvas.swallow_selected_with_undo)

        mw.edit_node_action = QAction("&Edit Node...", mw)
        mw.edit_node_action.setShortcut(QKeySequence("Ctrl+E"))
        mw.edit_node_action.triggered.connect(mw.edit_selected_node)

        mw.inspect_node_action = QAction("&Inspect Node...", mw)
        mw.inspect_node_action.setShortcut(QKeySequence("Ctrl+I"))
        mw.inspect_node_action.setStatusTip("Open node inspector for selected node")
        mw.inspect_node_action.triggered.connect(mw.inspect_selected_node)

        # Copy / Cut / Paste actions for canvas
        mw.copy_action = QAction("&Copy", mw)
        mw.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        mw.copy_action.triggered.connect(lambda: mw.canvas.copy_selected())

        mw.cut_action = QAction("Cu&t", mw)
        mw.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        mw.cut_action.triggered.connect(lambda: mw.canvas.cut_selected())

        mw.paste_action = QAction("&Paste", mw)
        mw.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        mw.paste_action.triggered.connect(lambda: mw.canvas.paste_clipboard())

        # Tools action: Rebuild Graph
        mw.rebuild_action = QAction("Rebuild &Graph", mw)
        mw.rebuild_action.setStatusTip(
            "Rebuild the graph from the canvas without running it"
        )
        mw.rebuild_action.triggered.connect(mw.rebuild_graph)

        # === Phase 3: Save Selection, Import Graph, Create Subgraph ===
        mw.save_selection_action = QAction("Save &Selection As...", mw)
        mw.save_selection_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        mw.save_selection_action.setStatusTip("Save selected nodes as a new graph file")
        mw.save_selection_action.triggered.connect(mw.save_selection_as_graph)

        mw.import_graph_action = QAction("Import &Into Current Canvas...", mw)
        mw.import_graph_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        mw.import_graph_action.setStatusTip(
            "Import a graph file and merge it into the current canvas"
        )
        mw.import_graph_action.triggered.connect(mw.import_graph_to_canvas)

        mw.create_subgraph_action = QAction("Create Sub-&Graph from Selection", mw)
        mw.create_subgraph_action.setShortcut(QKeySequence("Ctrl+G"))
        mw.create_subgraph_action.setStatusTip("Group selected nodes into a sub-graph")
        mw.create_subgraph_action.triggered.connect(mw.create_subgraph_from_selection)

    def create_menus(self):
        """Create menu bar."""
        mw = self.main_window
        menubar = mw.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(mw.new_action)
        file_menu.addAction(mw.open_action)
        file_menu.addAction(mw.import_graph_action)  # Phase 3: Import
        file_menu.addSeparator()
        file_menu.addAction(mw.save_action)
        file_menu.addAction(mw.save_selection_action)  # Phase 3: Save Selection
        file_menu.addSeparator()

        # Examples submenu
        examples_menu = file_menu.addMenu("&Examples")
        mw._populate_examples_menu(examples_menu)

        file_menu.addSeparator()
        file_menu.addAction(mw.exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(mw.undo_action)
        edit_menu.addAction(mw.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(mw.delete_action)
        edit_menu.addAction(mw.swallow_action)
        edit_menu.addAction(mw.copy_action)
        edit_menu.addAction(mw.cut_action)
        edit_menu.addAction(mw.paste_action)
        edit_menu.addAction(mw.edit_node_action)
        edit_menu.addSeparator()
        edit_menu.addAction(mw.create_subgraph_action)  # Phase 3: Ctrl+G

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        mlp_action = QAction("Generate &MLP...", mw)
        mlp_action.setShortcut(QKeySequence("Ctrl+M"))
        mlp_action.setStatusTip("Generate a new Multi-Layer Perceptron network")
        mlp_action.triggered.connect(mw._show_mlp_dialog)
        tools_menu.addAction(mlp_action)

        backprop_action = QAction("Add &Backpropagation...", mw)
        backprop_action.setShortcut(QKeySequence("Ctrl+B"))
        backprop_action.setStatusTip("Add backpropagation training to current MLP")
        backprop_action.triggered.connect(mw._show_backprop_dialog)
        tools_menu.addAction(backprop_action)

        # Create New Graph (dialog-driven)
        create_graph_action = QAction("Create &New Graph...", mw)
        create_graph_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        create_graph_action.setStatusTip("Create a new graph via dialog")
        create_graph_action.triggered.connect(mw._show_new_graph_dialog)
        tools_menu.addAction(create_graph_action)

        tools_menu.addSeparator()
        # Add rebuild action to Tools
        tools_menu.addAction(mw.rebuild_action)

        # Preferences (Colors / Theme)
        mw.preferences_action = QAction("&Preferences...", mw)
        mw.preferences_action.setShortcut(QKeySequence("Ctrl+,"))
        mw.preferences_action.setStatusTip("Open Preferences (Colors & Theme)")
        mw.preferences_action.triggered.connect(mw.show_preferences)
        # Put Preferences under Edit for discoverability
        try:
            edit_menu = menubar.actions()[1].menu()
            edit_menu.addSeparator()
            edit_menu.addAction(mw.preferences_action)
        except Exception:
            # Fallback: add to Tools
            tools_menu.addSeparator()
            tools_menu.addAction(mw.preferences_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        fit_view_action = QAction("&Fit All Nodes", mw)
        fit_view_action.setShortcut(QKeySequence("F"))
        fit_view_action.setStatusTip("Fit all nodes in view (F)")
        fit_view_action.triggered.connect(mw.canvas.fit_all_nodes_in_view)
        view_menu.addAction(fit_view_action)

        view_menu.addSeparator()
        view_menu.addAction(mw.palette.toggleViewAction())
        # Optional combined palette toggle (for testing / migration)
        try:
            view_menu.addAction(mw.combined_palette.toggleViewAction())
        except Exception:
            pass
        view_menu.addAction(mw.control_dock.toggleViewAction())
        # Console toggle (hidden by default)
        try:
            view_menu.addAction(mw.console_dock.toggleViewAction())
        except Exception:
            pass

    def create_toolbars(self):
        """Create toolbars."""
        mw = self.main_window

        toolbar = QToolBar("Main Toolbar")
        mw.addToolBar(toolbar)

        toolbar.addAction(mw.new_action)
        toolbar.addAction(mw.open_action)
        toolbar.addAction(mw.save_action)
        toolbar.addSeparator()
        toolbar.addAction(mw.delete_action)
        toolbar.addAction(mw.edit_node_action)
        toolbar.addSeparator()

        # Add Find Node search bar (use themed widgets when available)
        try:
            from ..theme_widgets import ThemedLabel, ThemedPushButton
        except Exception:
            ThemedLabel = None
            ThemedPushButton = None

        if ThemedLabel is not None:
            toolbar.addWidget(ThemedLabel("Find Node:"))
        else:
            toolbar.addWidget(QLabel("Find Node:"))

        mw.search_box = QLineEdit()
        mw.search_box.setPlaceholderText("Search by node name...")
        mw.search_box.setMaximumWidth(200)
        mw.search_box.returnPressed.connect(mw.find_node)
        mw.search_box.textChanged.connect(mw.highlight_matching_nodes)
        try:
            mw.search_box.setProperty("themed", True)
        except Exception:
            pass
        toolbar.addWidget(mw.search_box)

        if ThemedPushButton is not None:
            find_next_btn = ThemedPushButton("Next")
        else:
            find_next_btn = QPushButton("Next")
        find_next_btn.clicked.connect(mw.find_next_node)
        try:
            find_next_btn.setProperty("themed", True)
            find_next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            find_next_btn.setMouseTracking(True)
        except Exception:
            pass
        find_next_btn.setMaximumWidth(60)
        toolbar.addWidget(find_next_btn)

        # Track search results
        mw.search_results = []
        mw.search_index = -1

        # Rebuild Graph toolbar button removed from top toolbar — use Control Panel button
        # Add a small toolbar button for Add Selected to Plot
        # Keep this separate from the control panel's add_to_plot_btn to avoid overwriting it
        try:
            from ..theme_widgets import ThemedPushButton, ThemedToolButton
        except Exception:
            ThemedPushButton = None
            ThemedToolButton = None

        # Prefer tool-button for toolbar placement (matches native toolbar behavior)
        if ThemedToolButton is not None:
            mw.toolbar_add_to_plot_btn = ThemedToolButton()
            mw.toolbar_add_to_plot_btn.setText("add to plot")
        elif ThemedPushButton is not None:
            mw.toolbar_add_to_plot_btn = ThemedPushButton("add to plot")
        else:
            mw.toolbar_add_to_plot_btn = QPushButton("add to plot")
        try:
            mw.toolbar_add_to_plot_btn.setProperty("themed", True)
            mw.toolbar_add_to_plot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            mw.toolbar_add_to_plot_btn.setMouseTracking(True)
            # Ensure toolbar buttons are not styled flat by QToolBar defaults
            try:
                mw.toolbar_add_to_plot_btn.setFlat(False)
            except Exception:
                pass

            # Apply an inline style matching the control panel buttons for exact parity
            try:
                from ..theme import get_theme_manager

                tm = get_theme_manager()
                bg = tm.get_color("button_bg").name()
                txt = tm.get_color("text").name()
                hover = tm.get_color("button_hover").name()
                hover_border = tm.get_color("button_hover_border").name()
                radius = tm.theme.get("button_border_radius", "3px")
                # Choose selector based on widget type
                sel = (
                    "QToolButton"
                    if hasattr(mw.toolbar_add_to_plot_btn, "setArrowType")
                    else "QPushButton"
                )
                ss = (
                    f"{sel} {{ background-color: {bg}; color: {txt}; border: 1px solid transparent; padding: 6px 8px; border-radius: {radius}; }} "
                    f"{sel}:hover {{ background-color: {hover}; border: 1px solid {hover_border}; color: white; }}"
                )
                mw.toolbar_add_to_plot_btn.setStyleSheet(ss)
            except Exception:
                pass
        except Exception:
            pass
        mw.toolbar_add_to_plot_btn.setToolTip(
            "Add currently selected nodes to the plot window"
        )
        mw.toolbar_add_to_plot_btn.clicked.connect(mw.add_selected_to_plot)
        mw.toolbar_add_to_plot_btn.setMaximumWidth(140)
        try:
            # Prefer a compact fixed height in toolbars to avoid stretching in vertical toolbars
            mw.toolbar_add_to_plot_btn.setFixedHeight(28)
            from PyQt6.QtWidgets import QSizePolicy

            mw.toolbar_add_to_plot_btn.setSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
        except Exception:
            pass

        # Ensure it has an objectName so we can target it reliably in QSS
        try:
            mw.toolbar_add_to_plot_btn.setObjectName("toolbar_add_to_plot_btn")
        except Exception:
            pass

        # Put the add-to-plot button in its own section
        toolbar.addSeparator()
        toolbar.addWidget(mw.toolbar_add_to_plot_btn)

        # Apply inline style using the object selector to ensure exact parity
        try:
            from ..theme import get_theme_manager

            tm = get_theme_manager()
            bg = tm.get_color("button_bg").name()
            txt = tm.get_color("text").name()
            hover = tm.get_color("button_hover").name()
            hover_border = tm.get_color("button_hover_border").name()
            radius = tm.theme.get("button_border_radius", "3px")
            # Do not apply inline styles here; toolbar button should follow global themed QSS.
            # Inline styling was removed to keep styles canonical and driven by ThemeManager.
            pass
        except Exception:
            pass

        try:
            # Set cursor again after adding to toolbar in case platform/toolkit overrides it
            mw.toolbar_add_to_plot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        except Exception:
            pass

    def create_status_bar(self):
        """Create status bar."""
        mw = self.main_window
        mw.status_bar = QStatusBar()
        mw.setStatusBar(mw.status_bar)
        mw.status_bar.showMessage("Ready")
