from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)


class ReplaceNodeDialog(QDialog):
    """Simple dialog to select a node type for replacement. Returns node_type string."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Replace Node")
        self.resize(420, 400)
        layout = QVBoxLayout(self)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search node types...")
        layout.addWidget(self.search_bar)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        layout.addWidget(self.tree_widget)

        # Buttons - keep just Cancel to allow aborting. Selecting a node will auto-accept
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.cancel_btn.clicked.connect(self.reject)

        # Populate node categories. Import NodePalette to copy categories.
        try:
            from .node_palette import NodePalette

            palette = NodePalette()
            self.node_categories = palette.node_categories
        except Exception:
            # fallback to minimal list if palette is unavailable
            self.node_categories = {
                "Basic": {
                    "description": "Basic nodes",
                    "nodes": [
                        ("AdditionNode", "Addition", "Adds"),
                        ("MultiplicationNode", "Multiplication", "Multiply"),
                    ],
                }
            }

        self.all_items = []
        for category, data in self.node_categories.items():
            cat_item = QTreeWidgetItem([category])
            self.tree_widget.addTopLevelItem(cat_item)
            desc_item = QTreeWidgetItem([f"  {data.get('description', '')}"])
            desc_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            cat_item.addChild(desc_item)
            for node_type, display, desc in data.get("nodes", []):
                it = QTreeWidgetItem([f"{display}\n    {desc}"])
                it.setData(0, Qt.ItemDataRole.UserRole, node_type)
                it.setToolTip(0, f"{display}\n{desc}\nType: {node_type}")
                cat_item.addChild(it)
                self.all_items.append((it, cat_item))

        self.search_bar.textChanged.connect(self._filter)
        # Focus the search bar for immediate keyboard input
        try:
            self.search_bar.setFocus()
            self.search_bar.selectAll()
        except Exception:
            pass
        # Auto-accept when user clicks or activates a node type entry (leaf with UserRole)
        self.tree_widget.itemClicked.connect(self._on_item_activated)
        self.tree_widget.itemActivated.connect(self._on_item_activated)

    def _on_item_activated(self, item, column=0):
        # Only accept if this tree node has a 'UserRole' value (leaf node representing a type)
        t = item.data(0, Qt.ItemDataRole.UserRole)
        if t:
            # Select the item and accept the dialog so exec() returns True
            self.tree_widget.setCurrentItem(item)
            self.accept()

    def _filter(self, text: str):
        t = text.lower()
        if not t:
            for it, cat in self.all_items:
                it.setHidden(False)
            for i in range(self.tree_widget.topLevelItemCount()):
                self.tree_widget.topLevelItem(i).setHidden(False)
            return
        visible_categories = []
        for it, cat in self.all_items:
            name = it.text(0).lower()
            ntype = (it.data(0, Qt.ItemDataRole.UserRole) or "").lower()
            if t in name or t in ntype:
                it.setHidden(False)
                if cat not in visible_categories:
                    visible_categories.append(cat)
            else:
                it.setHidden(True)
        for i in range(self.tree_widget.topLevelItemCount()):
            cat = self.tree_widget.topLevelItem(i)
            cat.setHidden(cat not in visible_categories)

    def selected_type(self):
        item = self.tree_widget.currentItem()
        if not item:
            return None
        t = item.data(0, Qt.ItemDataRole.UserRole)
        return t
