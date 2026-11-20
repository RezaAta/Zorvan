try:
    from PyQt6.QtWidgets import (
        QLabel,
        QPushButton,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

from gui_framework.viewmodels.examples_loader_viewmodel import ExamplesLoaderViewModel

if HAS_PYQT:

    class ExamplesLoaderView(QWidget):
        def __init__(self, vm: ExamplesLoaderViewModel, parent=None):
            super().__init__(parent)
            self.vm = vm
            self.setWindowTitle("Examples")

            self.layout = QVBoxLayout(self)
            self.tree = QTreeWidget()
            self.tree.setHeaderHidden(True)
            self.layout.addWidget(self.tree)

            self.load_btn = QPushButton("Load")
            self.layout.addWidget(self.load_btn)

            self.preview = QLabel("")
            self.layout.addWidget(self.preview)

            self.load_btn.clicked.connect(self._on_load)
            self.tree.currentItemChanged.connect(self._on_select)

            self._refresh()

        def _refresh(self):
            self.tree.clear()
            cats = self.vm.list_examples_by_category()
            for cat in sorted(cats.keys()):
                parent = QTreeWidgetItem(self.tree)
                parent.setText(0, cat)
                parent.setFlags(parent.flags())
                for name, desc in cats[cat]:
                    child = QTreeWidgetItem(parent)
                    child.setText(0, name)
                    child.setData(0, 1, desc)  # store desc in column role 1
                self.tree.addTopLevelItem(parent)
            self.tree.expandAll()

        def _on_select(self, current, previous):
            if current is None:
                self.preview.setText("")
                return
            # only show preview for child items
            if current.parent() is None:
                self.preview.setText("")
            else:
                desc = current.data(0, 1)
                self.preview.setText(desc if desc else "")

        def _on_load(self):
            item = self.tree.currentItem()
            if item is None or item.parent() is None:
                return
            name = item.text(0)
            # Attempt to build/load the example via the ViewModel repository API
            built = None
            try:
                built = self.vm.build_example(name)
            except Exception:
                built = None
            if built is not None:
                self.preview.setText(f"Loaded: {name}")
            else:
                # Fallback to list_examples() to show path/desc
                path_desc = self.vm.list_examples().get(name, (None, None))
                path = path_desc[0] if path_desc else None
                self.preview.setText(f"Failed to load: {name}\n{path}")

else:

    class ExamplesLoaderView:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 is required to use ExamplesLoaderView")
