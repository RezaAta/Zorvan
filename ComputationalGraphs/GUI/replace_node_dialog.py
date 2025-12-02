from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

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

        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Populate node categories. Import NodePalette to copy categories.
        try:
            from .node_palette import NodePalette
            palette = NodePalette()
            self.node_categories = palette.node_categories
        except Exception:
            # fallback to minimal list if palette is unavailable
            self.node_categories = {
                "Basic": {"description": "Basic nodes", "nodes": [("AdditionNode","Addition","Adds"), ("MultiplicationNode","Multiplication","Multiply")]}
            }

        self.all_items = []
        for category, data in self.node_categories.items():
            cat_item = QTreeWidgetItem([category])
            self.tree_widget.addTopLevelItem(cat_item)
            desc_item = QTreeWidgetItem([f"  {data.get('description', '')}"])
            desc_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            cat_item.addChild(desc_item)
            for node_type, display, desc in data.get('nodes', []):
                it = QTreeWidgetItem([f"{display}\n    {desc}"])
                it.setData(0, Qt.ItemDataRole.UserRole, node_type)
                it.setToolTip(0, f"{display}\n{desc}\nType: {node_type}")
                cat_item.addChild(it)
                self.all_items.append((it, cat_item))

        self.search_bar.textChanged.connect(self._filter)

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
