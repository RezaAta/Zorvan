try:
    from PyQt6.QtWidgets import (
        QDialog,
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
    )

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel

if HAS_PYQT:

    class NodeEditorDialog(QDialog):
        def __init__(self, vm: NodeEditorViewModel, parent=None):
            super().__init__(parent)
            self.vm = vm
            self.setWindowTitle("Node Editor")
            self.layout = QVBoxLayout(self)
            self.form = QFormLayout()
            self.layout.addLayout(self.form)
            self._widgets = {}

            vm.observe_property("properties_changed", self._on_properties_changed)
            self._on_properties_changed(None, None)

            ok_btn = QPushButton("OK")
            ok_btn.clicked.connect(self.accept)
            self.layout.addWidget(ok_btn)

        def _on_properties_changed(self, old, new):
            # Rebuild form
            while self.form.rowCount() > 0:
                self.form.removeRow(0)
            self._widgets.clear()

            props = self.vm.get_properties()
            for k, v in props.items():
                editor = QLineEdit(str(v))
                self.form.addRow(QLabel(k), editor)
                self._widgets[k] = editor

        def accept(self) -> None:
            for k, w in self._widgets.items():
                val = w.text()
                try:
                    if val.isdigit():
                        val = int(val)
                    else:
                        val = float(val)
                except Exception:
                    pass
                self.vm.set_property(k, val)
            super().accept()

else:

    class NodeEditorDialog:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 is required to use NodeEditorDialog")
