try:
    from PyQt6.QtWidgets import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

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
            self.list = QListWidget()
            self.layout.addWidget(self.list)

            self.load_btn = QPushButton("Load")
            self.layout.addWidget(self.load_btn)

            self.preview = QLabel("")
            self.layout.addWidget(self.preview)

            self.load_btn.clicked.connect(self._on_load)
            self.list.currentTextChanged.connect(self._on_select)

            self._refresh()

        def _refresh(self):
            self.list.clear()
            examples = self.vm.list_examples()
            for name in sorted(examples.keys()):
                self.list.addItem(name)

        def _on_select(self, name):
            examples = self.vm.list_examples()
            if name in examples:
                _, desc = examples[name]
                self.preview.setText(desc)

        def _on_load(self):
            name = self.list.currentItem().text() if self.list.currentItem() else None
            if not name:
                return
            path, _ = self.vm.list_examples().get(name, (None, None))
            self.preview.setText(f"Selected: {name}\n{path}")

else:

    class ExamplesLoaderView:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 is required to use ExamplesLoaderView")
