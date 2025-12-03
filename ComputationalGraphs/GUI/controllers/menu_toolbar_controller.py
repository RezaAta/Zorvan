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

        mw.edit_node_action = QAction("&Edit Node...", mw)
        mw.edit_node_action.setShortcut(QKeySequence("Ctrl+E"))
        mw.edit_node_action.triggered.connect(mw.edit_selected_node)

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

    def create_menus(self):
        """Create menu bar."""
        mw = self.main_window
        menubar = mw.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(mw.new_action)
        file_menu.addAction(mw.open_action)
        file_menu.addAction(mw.save_action)
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
        edit_menu.addAction(mw.copy_action)
        edit_menu.addAction(mw.cut_action)
        edit_menu.addAction(mw.paste_action)
        edit_menu.addAction(mw.edit_node_action)

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
        tools_menu.addSeparator()
        # Add rebuild action to Tools
        tools_menu.addAction(mw.rebuild_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        fit_view_action = QAction("&Fit All Nodes", mw)
        fit_view_action.setShortcut(QKeySequence("F"))
        fit_view_action.setStatusTip("Fit all nodes in view (F)")
        fit_view_action.triggered.connect(mw.canvas.fit_all_nodes_in_view)
        view_menu.addAction(fit_view_action)

        view_menu.addSeparator()
        view_menu.addAction(mw.palette.toggleViewAction())
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

        # Add Find Node search bar
        toolbar.addWidget(QLabel("Find Node:"))
        mw.search_box = QLineEdit()
        mw.search_box.setPlaceholderText("Search by node name...")
        mw.search_box.setMaximumWidth(200)
        mw.search_box.returnPressed.connect(mw.find_node)
        mw.search_box.textChanged.connect(mw.highlight_matching_nodes)
        toolbar.addWidget(mw.search_box)

        find_next_btn = QPushButton("Next")
        find_next_btn.clicked.connect(mw.find_next_node)
        find_next_btn.setMaximumWidth(60)
        toolbar.addWidget(find_next_btn)

        # Track search results
        mw.search_results = []
        mw.search_index = -1

        # Rebuild Graph toolbar button removed from top toolbar — use Control Panel button
        # Add a small toolbar button for Add Selected to Plot
        # Keep this separate from the control panel's add_to_plot_btn to avoid overwriting it
        mw.toolbar_add_to_plot_btn = QPushButton("add to plot")
        mw.toolbar_add_to_plot_btn.setToolTip(
            "Add currently selected nodes to the plot window"
        )
        mw.toolbar_add_to_plot_btn.clicked.connect(mw.add_selected_to_plot)
        mw.toolbar_add_to_plot_btn.setMaximumWidth(140)
        # Put the add-to-plot button in its own section
        toolbar.addSeparator()
        toolbar.addWidget(mw.toolbar_add_to_plot_btn)

    def create_status_bar(self):
        """Create status bar."""
        mw = self.main_window
        mw.status_bar = QStatusBar()
        mw.setStatusBar(mw.status_bar)
        mw.status_bar.showMessage("Ready")
