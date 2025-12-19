import warnings

from .combined_node_palette import CombinedNodePalette as NodePalette

warnings.warn(
    "NodePalette is deprecated; use CombinedNodePalette instead", DeprecationWarning
)


from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtGui import QBrush, QCursor, QDrag, QFont
from PyQt6.QtWidgets import (
    QDockWidget,
    QMenu,
    QMessageBox,
    QStyle,
    QTreeWidget,
    QTreeWidgetItem,
)

try:
    from PyQt6.QtWidgets import QAction
except Exception:
    # Some PyQt6 builds provide QAction under QtGui
    from PyQt6.QtGui import QAction

from .theme_utils import ThemeMixin


class NodePalette(QDockWidget, ThemeMixin):
    """Dockable palette showing available node types."""

    def __init__(self, parent=None):
        super().__init__("Node Palette", parent)

        # Create main widget and layout
        from PyQt6.QtWidgets import (
            QHBoxLayout,
            QLineEdit,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Add search and create custom button
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search nodes...")
        self.search_bar.textChanged.connect(self.filter_nodes)
        search_layout.addWidget(self.search_bar)

        self.create_custom_button = QPushButton("Create")
        try:
            self.create_custom_button.setProperty("themed", True)
            self.create_custom_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.create_custom_button.setMouseTracking(True)
        except Exception:
            pass
        try:
            from .controllers.control_panel_builder import _apply_icon

            _apply_icon(
                self,
                self.create_custom_button,
                "fa5s.plus",
                QStyle.StandardPixmap.SP_FileDialogNewFolder,
                14,
            )
        except Exception:
            pass
        self.create_custom_button.setMinimumWidth(110)
        self.create_custom_button.setMaximumWidth(180)
        self.create_custom_button.clicked.connect(self.on_create_custom_node)
        search_layout.addWidget(self.create_custom_button)

        layout.addLayout(search_layout)

        # Add tree widget for grouped nodes
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(15)
        self.tree_widget.setUniformRowHeights(False)  # Allow varying row heights
        # Use theme for palette body and text (handled by ThemeMixin.apply_theme)
        try:
            # Initialize ThemeMixin to subscribe to theme changes and call apply_theme()
            ThemeMixin.__init__(self)
        except Exception:
            pass
        # Also ensure we have a direct connection to the ThemeManager so tests and
        # runtime theme changes reliably invoke our apply_theme implementation.
        try:
            from .theme import get_theme_manager

            get_theme_manager().theme_changed.connect(self.apply_theme)
        except Exception:
            pass

        # Finish widget setup and populate nodes
        layout.addWidget(self.tree_widget)

        self.setWidget(main_widget)

        # Organize nodes into categories with descriptions
        self.node_categories = {
            "Basic Operations": {
                "description": "Fundamental arithmetic operations",
                "nodes": [
                    ("AdditionNode", "Addition", "Adds multiple input values"),
                    (
                        "SubtractionNode",
                        "Subtraction",
                        "Subtracts second input from first",
                    ),
                    ("MultiplicationNode", "Multiplication", "Multiplies input values"),
                    ("DivisionNode", "Division", "Divides first input by second"),
                ],
            },
            "Data & Buffers": {
                "description": "Data sources and storage containers",
                "nodes": [
                    (
                        "DataStreamNode",
                        "Data Stream",
                        "Provides sequential data from a source",
                    ),
                    (
                        "DynamicDataStreamNode",
                        "Dynamic Data Stream",
                        "Dynamic data source with runtime updates",
                    ),
                    ("BufferNode", "Buffer", "Stores and manages recent values"),
                    (
                        "MovingAverageNode",
                        "Moving Average",
                        "Calculates average of buffered values (continuous or batch mode)",
                    ),
                    ("SequencerNode", "Sequencer", "Sequences multiple inputs"),
                    ("ListNode", "List", "Collects inputs into a list structure"),
                    ("ContainerNode", "Container", "General-purpose data container"),
                    (
                        "InitializableContainerNode",
                        "Container (Init)",
                        "Container node with initializable/random value (weights)",
                    ),
                    (
                        "ExtractListElement",
                        "Extract List Element",
                        "Extracts element from list by index",
                    ),
                ],
            },
            "Activation Functions": {
                "description": "Neural network activation functions",
                "nodes": [
                    ("SigmoidNode", "Sigmoid", "Sigmoid activation function"),
                    (
                        "SigmoidDerivativeNode",
                        "Sigmoid'",
                        "Derivative of sigmoid function",
                    ),
                    ("ReLUNode", "ReLU", "Rectified Linear Unit activation"),
                    ("ReLUDerivativeNode", "ReLU'", "Derivative of ReLU function"),
                    ("LinearNode", "Linear", "Linear activation (identity)"),
                    (
                        "LinearNodeDerivative",
                        "Linear'",
                        "Derivative of linear function",
                    ),
                    ("TanhNode", "Tanh", "Hyperbolic tangent activation function"),
                    (
                        "TanhDerivativeNode",
                        "Tanh'",
                        "Derivative of hyperbolic tangent function",
                    ),
                    ("GaussianNode", "Gaussian", "Gaussian (bell curve) function"),
                    (
                        "PiecewiseLinearNode",
                        "Piecewise Linear",
                        "Piecewise linear function",
                    ),
                ],
            },
            "Loss Functions": {
                "description": "Error and loss calculations (buffer-style)",
                "nodes": [
                    (
                        "MeanSquaredNode",
                        "MS",
                        "Buffer-based Mean Squared (mean of squared buffered values). Single-input node; supports continuous or batch modes.",
                    ),
                ],
            },
            "Statistical": {
                "description": "Statistical operations and aggregations",
                "nodes": [
                    ("MaxNode", "Maximum", "Returns the maximum value from inputs"),
                    ("MinNode", "Minimum", "Returns the minimum value from inputs"),
                ],
            },
            "Evolutionary Algorithms": {
                "description": "Genetic algorithm and optimization nodes",
                "nodes": [
                    (
                        "PopulationNode",
                        "Population",
                        "Auto-generating GA population node",
                    ),
                    (
                        "TournamentSelectionNode",
                        "Tournament Selection",
                        "Selects best individuals via tournament",
                    ),
                    (
                        "BulkTournamentNode",
                        "Bulk Tournament",
                        "Bulk tournament selection operation",
                    ),
                    (
                        "CrossoverNode",
                        "Crossover",
                        "Genetic crossover of two individuals",
                    ),
                    (
                        "SingleCrossoverNode",
                        "Single Crossover",
                        "Single-point crossover operation",
                    ),
                    (
                        "SingleInputCrossover",
                        "Single Input Crossover",
                        "Crossover with single input",
                    ),
                    ("MutationNode", "Mutation", "Random genetic mutation"),
                    (
                        "ElitismNode",
                        "Elitism",
                        "Preserves best individual across generations",
                    ),
                    (
                        "DeJongSphereNode",
                        "De Jong Sphere",
                        "De Jong sphere fitness function",
                    ),
                ],
            },
            "Utility Nodes": {
                "description": "Utility and I/O nodes",
                "nodes": [
                    ("DisplayNode", "Display", "Prints values to console or log"),
                ],
            },
        }

        # Populate tree with categories and nodes
        self.all_items = []  # Keep track of all items for search
        self.custom_node_items = []  # Track custom node items for refresh
        self.refresh_custom_nodes()
        for category, category_data in self.node_categories.items():
            # Create category header
            category_item = QTreeWidgetItem([category])
            category_font = QFont()
            category_font.setBold(True)
            category_font.setPointSize(10)
            category_item.setFont(0, category_font)
            category_item.setExpanded(True)  # Expand by default
            self.tree_widget.addTopLevelItem(category_item)

            # Add category description as a child (non-draggable)
            desc_item = QTreeWidgetItem([f"  {category_data['description']}"])
            desc_font = QFont()
            desc_font.setItalic(True)
            desc_font.setPointSize(8)
            desc_item.setFont(0, desc_font)
            desc_item.setForeground(0, Qt.GlobalColor.gray)
            desc_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not selectable or draggable
            category_item.addChild(desc_item)

            # Add nodes
            for node_type, display_name, description in category_data["nodes"]:
                node_item = QTreeWidgetItem([f"{display_name}\n    {description}"])
                node_item.setData(0, Qt.ItemDataRole.UserRole, node_type)
                node_item.setToolTip(
                    0, f"{display_name}\n{description}\n\nNode Type: {node_type}"
                )
                category_item.addChild(node_item)
                self.all_items.append((node_item, category_item))

        # Enable drag
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        # Context menu for editing/deleting custom nodes
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.on_context_menu)

        # Custom drag handler
        self.tree_widget.startDrag = self.start_drag

    def apply_theme(self):
        """Apply theme colors to node palette widgets (called by ThemeMixin)."""
        try:
            tm = self.get_theme_manager()
            list_bg = tm.get_color("list_bg", "#313335").name()
            border = tm.get_color("border", "#555555").name()
            text_col = tm.get_color("text", "#bbbbbb").name()
            # Use inline stylesheet so tests can observe the applied color values
            ss = f"QTreeWidget {{ background-color: {list_bg}; border: 1px solid {border}; color: {text_col}; }}"
            try:
                self.tree_widget.setStyleSheet(ss)
                # Ensure UI updates propagate in tests
                try:
                    from PyQt6.QtWidgets import QApplication

                    app = QApplication.instance()
                    if app is not None:
                        app.processEvents()
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

    # Theme handling is implemented in `apply_theme()` via ThemeMixin
    # (keeps behavior centralized and easier to test).
    def filter_nodes(self, text):
        """Filter node list based on search text."""
        search_text = text.lower()

        if not search_text:
            # Show all items if search is empty
            for node_item, category_item in self.all_items:
                node_item.setHidden(False)
                category_item.setHidden(False)
            # Show all categories and their description items
            for i in range(self.tree_widget.topLevelItemCount()):
                category = self.tree_widget.topLevelItem(i)
                category.setHidden(False)
                category.setExpanded(True)
                # Show description item (first child)
                if category.childCount() > 0:
                    category.child(0).setHidden(False)
            return

        # Track which categories have visible items (use list instead of set)
        visible_categories = []

        # Filter nodes
        for node_item, category_item in self.all_items:
            node_text = node_item.text(0).lower()
            node_type = node_item.data(0, Qt.ItemDataRole.UserRole)

            if node_type:
                node_type_lower = node_type.lower()
            else:
                node_type_lower = ""

            # Show if search matches display name or node type
            if search_text in node_text or search_text in node_type_lower:
                node_item.setHidden(False)
                if category_item not in visible_categories:
                    visible_categories.append(category_item)
                category_item.setExpanded(True)  # Expand when searching
            else:
                node_item.setHidden(True)

        # Hide categories with no visible children, hide their description items when searching
        for i in range(self.tree_widget.topLevelItemCount()):
            category = self.tree_widget.topLevelItem(i)
            if category in visible_categories:
                category.setHidden(False)
                # Hide description when searching (less clutter)
                if category.childCount() > 0:
                    category.child(0).setHidden(True)
            else:
                category.setHidden(True)

    def start_drag(self, supported_actions):
        """Start drag operation with node type data."""
        item = self.tree_widget.currentItem()
        if not item:
            return

        # Only drag node items, not category items
        node_type = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_type:
            return

        drag = QDrag(self.tree_widget)
        mime_data = QMimeData()
        mime_data.setText(node_type)
        drag.setMimeData(mime_data)

        drag.exec(Qt.DropAction.CopyAction)

    def refresh_custom_nodes(self):
        """Refresh custom nodes list from manager."""
        from ComputationalGraphs.GUI.custom_node_manager import get_custom_node_manager

        manager = get_custom_node_manager()
        custom_types = manager.get_type_names()

        # Ensure the Custom Nodes category exists before updating
        if "Custom Nodes" not in self.node_categories:
            self.node_categories["Custom Nodes"] = {
                "description": "User-defined custom nodes",
                "nodes": [],
            }

        # Clear and update custom nodes in category
        self.node_categories["Custom Nodes"]["nodes"] = [
            (type_name, type_name, manager.get_definition(type_name).description)
            for type_name in custom_types
        ]

    def on_create_custom_node(self):
        """Open dialog to create a new custom node."""
        from ComputationalGraphs.GUI.custom_node_dialog import CustomNodeDialog
        from ComputationalGraphs.GUI.custom_node_manager import get_custom_node_manager

        dialog = CustomNodeDialog(parent=self)
        if dialog.exec():
            definition = dialog.definition
            manager = get_custom_node_manager()

            try:
                manager.add_definition(definition)
                manager.register_with_factory()
                manager.save_library()
                self.refresh_palette()
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.critical(
                    self,
                    "Error Saving Custom Node",
                    f"Failed to save custom node: {e}",
                )

    def refresh_palette(self):
        """Refresh the entire palette (used after adding custom nodes)."""
        self.refresh_custom_nodes()

        # Rebuild the tree widget
        self.tree_widget.clear()
        self.all_items = []
        self.custom_node_items = []

        for category, category_data in self.node_categories.items():
            # Create category header
            category_item = QTreeWidgetItem([category])
            category_font = QFont()
            category_font.setBold(True)
            category_font.setPointSize(10)
            category_item.setFont(0, category_font)
            category_item.setExpanded(True)
            self.tree_widget.addTopLevelItem(category_item)

            # Add category description as a child (non-draggable)
            desc_item = QTreeWidgetItem([f"  {category_data['description']}"])
            desc_font = QFont()
            desc_font.setItalic(True)
            desc_font.setPointSize(8)
            desc_item.setFont(0, desc_font)
            desc_item.setForeground(0, QBrush(Qt.GlobalColor.gray))
            desc_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            category_item.addChild(desc_item)

            # Add nodes
            for node_type, display_name, description in category_data["nodes"]:
                node_item = QTreeWidgetItem([f"{display_name}\n    {description}"])
                node_item.setData(0, Qt.ItemDataRole.UserRole, node_type)
                node_item.setToolTip(
                    0, f"{display_name}\n{description}\n\nNode Type: {node_type}"
                )
                category_item.addChild(node_item)
                self.all_items.append((node_item, category_item))

                if category == "Custom Nodes":
                    self.custom_node_items.append(node_item)
                    # Allow right-click context menu to edit/delete custom nodes
                    node_item.setFlags(node_item.flags() | Qt.ItemFlag.ItemIsSelectable)

    def on_context_menu(self, position):
        """Show context menu for custom node items to edit/delete."""
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        node_type = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_type:
            return

        # Only allow editing/deleting for custom nodes
        from ComputationalGraphs.GUI.custom_node_manager import get_custom_node_manager

        manager = get_custom_node_manager()
        if node_type not in manager.get_type_names():
            return

        menu = QMenu(self)
        edit_action = QAction("Edit Custom Node", self)
        delete_action = QAction("Delete Custom Node", self)
        menu.addAction(edit_action)
        menu.addAction(delete_action)

        def on_edit():
            from ComputationalGraphs.GUI.custom_node_dialog import CustomNodeDialog

            definition = manager.get_definition(node_type)
            dialog = CustomNodeDialog(parent=self, existing_definition=definition)
            if dialog.exec():
                new_def = dialog.definition
                # If the type name changed, remove the old definition
                if new_def.type_name != node_type:
                    manager.remove_definition(node_type)
                manager.add_definition(new_def)
                manager.register_with_factory()
                manager.save_library()
                self.refresh_palette()

        def on_delete():
            reply = QMessageBox.question(
                self,
                "Delete Custom Node",
                f"Are you sure you want to delete custom node '{node_type}'?\nThis will NOT remove any existing nodes of this type from open graphs.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                manager.remove_definition(node_type)
                manager.save_library()
                self.refresh_palette()

        edit_action.triggered.connect(on_edit)
        delete_action.triggered.connect(on_delete)
        menu.exec(QCursor.pos())
