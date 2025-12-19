"""
PlotConfigView: PyQt6 UI for plot configuration dialog.

This view provides the user interface for configuring plot settings,
binding to PlotConfigViewModel for reactive state management.
"""

try:
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
    )

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

    class QDialog:
        def __init__(self, parent=None):
            pass


from ..viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from .base import BaseView

    class PlotConfigView(BaseView, QDialog):
        """
        PyQt6 dialog for plot configuration.

        Features:
        - Node selection with checkboxes
        - Graph/subgraph filtering
        - Max iterations setting
        - Select all/none functionality
        - Real-time filtering

        Example:
            >>> from gui_framework.viewmodels.plot_config_viewmodel import PlotConfigViewModel, NodeInfo
            >>> vm = PlotConfigViewModel(max_iterations=100)
            >>> # Load nodes
            >>> nodes = [NodeInfo(name="A", node_id="node_a"), NodeInfo(name="B", node_id="node_b")]
            >>> vm.load_nodes(nodes)
            >>> # Show dialog
            >>> view = PlotConfigView(vm, parent=main_window)
            >>> if view.exec() == QDialog.DialogCode.Accepted:
            ...     selected = vm.get_selected_nodes()
        """

        def __init__(self, viewmodel: BaseViewModel, parent=None):
            """
            Initialize PlotConfigView.

            Args:
                viewmodel: PlotConfigViewModel instance
                parent: Parent Qt widget
            """
            QDialog.__init__(self, parent)
            BaseView.__init__(self, viewmodel, parent)
            self.setWindowTitle("Configure Plot")
            self.setModal(True)
            self.resize(400, 500)
            self._setup_ui()
            self._connect_signals()

        def _setup_ui(self):
            """Create and layout the UI widgets."""
            layout = QVBoxLayout(self)

            # Filter section
            filter_layout = QHBoxLayout()
            filter_layout.addWidget(QLabel("Filter by:"))

            self.filter_combo = QComboBox()
            self.filter_combo.addItem("All Nodes", "all")
            self.filter_combo.addItem("Mother Graph Only", "mother")

            # Add subgraphs
            for subgraph_name in self.viewmodel.get_subgraph_names():
                self.filter_combo.addItem(f"SubGraph: {subgraph_name}", subgraph_name)

            self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
            filter_layout.addWidget(self.filter_combo)
            filter_layout.addStretch()
            layout.addLayout(filter_layout)

            # Instructions
            instructions = QLabel("Select nodes to plot:")
            layout.addWidget(instructions)

            # Node list with checkboxes
            self.node_list = QListWidget()
            self.node_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
            self.node_list.setSpacing(2)
            layout.addWidget(self.node_list)

            # Selection buttons
            selection_layout = QHBoxLayout()

            self.select_all_button = QPushButton("Select All")
            self.select_all_button.clicked.connect(self._on_select_all)
            selection_layout.addWidget(self.select_all_button)

            self.select_none_button = QPushButton("Select None")
            self.select_none_button.clicked.connect(self._on_select_none)
            selection_layout.addWidget(self.select_none_button)

            selection_layout.addStretch()
            layout.addLayout(selection_layout)

            # Max iterations section
            iter_layout = QHBoxLayout()
            iter_layout.addWidget(QLabel("Max iterations:"))

            self.max_iter_spin = QSpinBox()
            self.max_iter_spin.setMinimum(10)
            self.max_iter_spin.setMaximum(100000)
            self.max_iter_spin.setValue(self.viewmodel.get_max_iterations())
            self.max_iter_spin.setSingleStep(10)
            self.max_iter_spin.valueChanged.connect(self._on_max_iter_changed)
            iter_layout.addWidget(self.max_iter_spin)
            iter_layout.addStretch()
            layout.addLayout(iter_layout)

            # Selection count label
            self.selection_label = QLabel("Selected: 0 nodes")
            layout.addWidget(self.selection_label)

            # Dialog buttons
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            layout.addWidget(button_box)

            # Initial population
            self._populate_node_list()

        def _connect_signals(self):
            """Connect ViewModel signals to View updates."""
            # Observe ViewModel changes
            self.viewmodel.nodes_changed.observe(self._on_nodes_changed)
            self.viewmodel.selection_changed.observe(self._on_selection_changed)
            self.viewmodel.filter_changed.observe(self._on_filter_updated)

        def _populate_node_list(self):
            """Populate node list with checkboxes."""
            self.node_list.clear()

            for node_info in self.viewmodel.get_filtered_nodes():
                item = QListWidgetItem(node_info.name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

                # Set checked state from viewmodel
                if self.viewmodel.is_node_selected(node_info.name):
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)

                # Store node name in item data
                item.setData(Qt.ItemDataRole.UserRole, node_info.name)

                self.node_list.addItem(item)

            # Connect item changed signal
            self.node_list.itemChanged.connect(self._on_item_checked)

            # Update selection label
            self._update_selection_label()

        def _on_filter_changed(self, index: int):
            """Handle filter combo box change."""
            filter_mode = self.filter_combo.itemData(index)
            self.viewmodel.set_filter(filter_mode)

        def _on_item_checked(self, item: QListWidgetItem):
            """Handle node checkbox state change."""
            node_name = item.data(Qt.ItemDataRole.UserRole)
            if item.checkState() == Qt.CheckState.Checked:
                self.viewmodel.select_node(node_name)
            else:
                self.viewmodel.deselect_node(node_name)

        def _on_select_all(self):
            """Handle select all button click."""
            self.viewmodel.select_all_visible()

        def _on_select_none(self):
            """Handle select none button click."""
            self.viewmodel.deselect_all()

        def _on_max_iter_changed(self, value: int):
            """Handle max iterations spin box change."""
            self.viewmodel.set_max_iterations(value)

        def _on_nodes_changed(self, _):
            """Handle nodes changed in ViewModel."""
            self._populate_node_list()

        def _on_selection_changed(self, _):
            """Handle selection changed in ViewModel."""
            # Update checkboxes without triggering signals
            self.node_list.itemChanged.disconnect(self._on_item_checked)

            for i in range(self.node_list.count()):
                item = self.node_list.item(i)
                node_name = item.data(Qt.ItemDataRole.UserRole)

                if self.viewmodel.is_node_selected(node_name):
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)

            self.node_list.itemChanged.connect(self._on_item_checked)

            # Update label
            self._update_selection_label()

        def _on_filter_updated(self, _):
            """Handle filter changed in ViewModel."""
            self._populate_node_list()

        def _update_selection_label(self):
            """Update selection count label."""
            count = self.viewmodel.get_selection_count()
            self.selection_label.setText(f"Selected: {count} nodes")

else:
    # Stub for testing without PyQt6
    class PlotConfigView:
        def __init__(self, viewmodel, parent=None):
            self.viewmodel = viewmodel
