"""MVVM Replace Node dialog: search and select a node type."""

try:
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

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

from ...viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from gui_framework.viewmodels.dialogs.replace_node_viewmodel import (
        ReplaceNodeViewModel,
    )

    from ..base import BaseView

    class ReplaceNodeDialog(QDialog, BaseView):
        def __init__(self, viewmodel: BaseViewModel, parent=None):
            QDialog.__init__(self, parent)
            BaseView.__init__(self, viewmodel, parent)
            self.setWindowTitle("Replace Node")
            self.resize(420, 400)

            self._setup_ui()
            # Bind synchronously if VM already initialized
            try:
                self._bind_viewmodel()
            except Exception:
                pass

        def _setup_ui(self):
            layout = QVBoxLayout(self)

            self.search_bar = QLineEdit()
            self.search_bar.setPlaceholderText("Search node types...")
            layout.addWidget(self.search_bar)

            self.tree_widget = QTreeWidget()
            self.tree_widget.setHeaderHidden(True)
            layout.addWidget(self.tree_widget)

            btn_layout = QHBoxLayout()
            self.cancel_btn = QPushButton("Cancel")
            btn_layout.addStretch()
            btn_layout.addWidget(self.cancel_btn)
            layout.addLayout(btn_layout)

            self.cancel_btn.clicked.connect(self.reject)

            # Hook search changes
            self.search_bar.textChanged.connect(
                lambda t: self.get_viewmodel().set_search_text(t)
            )
            self.search_bar.setFocus()

            self.tree_widget.itemClicked.connect(self._on_item_activated)
            self.tree_widget.itemActivated.connect(self._on_item_activated)

        def _bind_viewmodel(self):
            vm: ReplaceNodeViewModel = self.get_viewmodel()
            vm.observe_property("categories_changed", lambda o, n: self._rebuild_tree())
            # Initial population
            self._rebuild_tree()

        def _rebuild_tree(self):
            self.tree_widget.clear()
            vm: ReplaceNodeViewModel = self.get_viewmodel()
            items_by_cat = {}
            for cat, type_name, display, desc in vm.get_filtered():
                if cat not in items_by_cat:
                    cat_item = QTreeWidgetItem([cat])
                    self.tree_widget.addTopLevelItem(cat_item)
                    items_by_cat[cat] = cat_item
                    # add description
                    desc_item = QTreeWidgetItem([f"  {desc}"])
                    # Make description non-selectable
                    try:
                        desc_item.setFlags(
                            desc_item.flags() & ~Qt.ItemFlag.ItemIsSelectable
                        )
                    except Exception:
                        pass
                    items_by_cat[cat].addChild(desc_item)
                it = QTreeWidgetItem([f"{display}\n    {desc}"])
                it.setData(0, Qt.ItemDataRole.UserRole, type_name)
                items_by_cat[cat].addChild(it)

        def _on_item_activated(self, item, column=0):
            t = item.data(0, Qt.ItemDataRole.UserRole)
            if t:
                self.tree_widget.setCurrentItem(item)
                self.accept()

        def selected_type(self):
            item = self.tree_widget.currentItem()
            if not item:
                return None
            return item.data(0, Qt.ItemDataRole.UserRole)

else:

    class ReplaceNodeDialog:
        def __init__(self, vm, parent=None):
            self.viewmodel = vm

        def exec(self):
            return 0

        def selected_type(self):
            return None


if PYQT_AVAILABLE:
    try:
        ReplaceNodeDialog.__abstractmethods__ = set()
    except Exception:
        pass
