"""
Palette widget showing available node types for drag-and-drop.
"""

from PyQt6.QtWidgets import QDockWidget, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag, QFont


class NodePalette(QDockWidget):
    """Dockable palette showing available node types."""
    
    def __init__(self, parent=None):
        super().__init__("Node Palette", parent)
        
        # Create main widget and layout
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Add search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search nodes...")
        self.search_bar.textChanged.connect(self.filter_nodes)
        layout.addWidget(self.search_bar)
        
        # Add tree widget for grouped nodes
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(15)
        self.tree_widget.setUniformRowHeights(False)  # Allow varying row heights
        layout.addWidget(self.tree_widget)
        
        self.setWidget(main_widget)
        
        # Organize nodes into categories with descriptions
        self.node_categories = {
            "Basic Operations": {
                "description": "Fundamental arithmetic operations",
                "nodes": [
                    ("AdditionNode", "Addition", "Adds multiple input values"),
                    ("SubtractionNode", "Subtraction", "Subtracts second input from first"),
                    ("MultiplicationNode", "Multiplication", "Multiplies input values"),
                    ("DivisionNode", "Division", "Divides first input by second"),
                ]
            },
            "Data & Buffers": {
                "description": "Data sources and storage containers",
                "nodes": [
                    ("DataStreamNode", "Data Stream", "Provides sequential data from a source"),
                    ("DynamicDataStreamNode", "Dynamic Data Stream", "Dynamic data source with runtime updates"),
                    ("BufferNode", "Buffer", "Stores and manages recent values"),
                    ("MovingAverageNode", "Moving Average", "Calculates average of buffered values (continuous or batch mode)"),
                    ("SequencerNode", "Sequencer", "Sequences multiple inputs"),
                    ("ListNode", "List", "Collects inputs into a list structure"),
                    ("ContainerNode", "Container", "General-purpose data container"),
                    ("ExtractListElement", "Extract List Element", "Extracts element from list by index"),
                ]
            },
            "Activation Functions": {
                "description": "Neural network activation functions",
                "nodes": [
                    ("SigmoidNode", "Sigmoid", "Sigmoid activation function"),
                    ("SigmoidDerivativeNode", "Sigmoid'", "Derivative of sigmoid function"),
                    ("ReLUNode", "ReLU", "Rectified Linear Unit activation"),
                    ("ReLUDerivativeNode", "ReLU'", "Derivative of ReLU function"),
                    ("LinearNode", "Linear", "Linear activation (identity)"),
                    ("LinearNodeDerivative", "Linear'", "Derivative of linear function"),
                    ("GaussianNode", "Gaussian", "Gaussian (bell curve) function"),
                    ("PiecewiseLinearNode", "Piecewise Linear", "Piecewise linear function"),
                ]
            },
            "Loss Functions": {
                "description": "Error and loss calculations (buffer-style)",
                "nodes": [
                    ("MeanSquaredErrorNode", "MSE", "Buffer-based MSE (mean of squared buffered values). Single-input node; supports continuous or batch modes."),
                ]
            },
            "Statistical": {
                "description": "Statistical operations and aggregations",
                "nodes": [
                    ("MaxNode", "Maximum", "Returns the maximum value from inputs"),
                    ("MinNode", "Minimum", "Returns the minimum value from inputs"),
                ]
            },
            "Evolutionary Algorithms": {
                "description": "Genetic algorithm and optimization nodes",
                "nodes": [
                    ("PopulationNode", "Population", "Auto-generating GA population node"),
                    ("TournamentSelectionNode", "Tournament Selection", "Selects best individuals via tournament"),
                    ("BulkTournamentNode", "Bulk Tournament", "Bulk tournament selection operation"),
                    ("CrossoverNode", "Crossover", "Genetic crossover of two individuals"),
                    ("SingleCrossoverNode", "Single Crossover", "Single-point crossover operation"),
                    ("SingleInputCrossover", "Single Input Crossover", "Crossover with single input"),
                    ("MutationNode", "Mutation", "Random genetic mutation"),
                    ("ElitismNode", "Elitism", "Preserves best individual across generations"),
                    ("DeJongSphereNode", "De Jong Sphere", "De Jong sphere fitness function"),
                ]
            },
            "Utility": {
                "description": "Helper and visualization nodes",
                "nodes": [
                    ("BufferNode", "Buffer", "Stores values (set allowNone=False to filter None)"),
                    ("DisplayNode", "Display", "Prints values to console output"),
                ]
            },
        }
        
        # Populate tree with categories and nodes
        self.all_items = []  # Keep track of all items for search
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
            for node_type, display_name, description in category_data['nodes']:
                node_item = QTreeWidgetItem([f"{display_name}\n    {description}"])
                node_item.setData(0, Qt.ItemDataRole.UserRole, node_type)
                node_item.setToolTip(0, f"{display_name}\n{description}\n\nNode Type: {node_type}")
                category_item.addChild(node_item)
                self.all_items.append((node_item, category_item))
        
        # Enable drag
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        
        # Custom drag handler
        self.tree_widget.startDrag = self.start_drag
    
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
