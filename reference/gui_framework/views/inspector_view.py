try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

from typing import Optional

from gui_framework.viewmodels.inspector_viewmodel import InspectorViewModel

if HAS_PYQT:

    class InspectorView(QWidget):
        """Simple Inspector view that binds to an InspectorViewModel."""

        def __init__(self, vm: InspectorViewModel, parent=None):
            super().__init__(parent)
            self.vm = vm
            self.setWindowTitle("Inspector")
            self.layout = QVBoxLayout(self)
            self.form = QFormLayout()
            self.layout.addLayout(self.form)

            self._widgets = {}

            # Observe viewmodel
            vm.observe_property("properties_changed", self._on_properties_changed)
            self._on_properties_changed(None, None)

        def _on_properties_changed(self, old, new):
            # Clear form
            while self.form.rowCount() > 0:
                self.form.removeRow(0)
            self._widgets.clear()

            props = self.vm.get_properties()
            for k, v in props.items():
                lbl = QLabel(k)
                editor = QLineEdit(str(v))
                self.form.addRow(lbl, editor)
                self._widgets[k] = editor

            # Add apply button
            apply_btn = QPushButton("Apply")
            apply_btn.clicked.connect(self._apply)
            self.layout.addWidget(apply_btn)

        def _apply(self):
            for k, widget in self._widgets.items():
                text = widget.text()
                # Try to coerce numeric types
                val = text
                try:
                    if text.isdigit():
                        val = int(text)
                    else:
                        f = float(text)
                        val = f
                except Exception:
                    pass

                self.vm.set_property(k, val)

else:

    class InspectorView:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 is required to use InspectorView")
