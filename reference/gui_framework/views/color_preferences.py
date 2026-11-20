"""
Color Preferences dialog — allows changing default colors used by the UI.
"""

try:
    from PyQt6.QtWidgets import (
        QColorDialog,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
    )

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False


if PYQT_AVAILABLE:

    class ColorPreferencesDialog(QDialog):
        def __init__(self, main_window, parent=None):
            super().__init__(parent or main_window)
            self.main_window = main_window
            self.setWindowTitle("Preferences — Colors")
            self.resize(420, 220)

            self._setup_ui()
            self._populate_from_main_window()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            self.min_color_edit = QLineEdit()
            self.min_color_btn = QPushButton("Pick...")
            self.min_color_btn.clicked.connect(
                lambda: self._pick_color(self.min_color_edit)
            )
            form.addRow(
                QLabel("Min gradient color (hex):"),
                self._hbox(self.min_color_edit, self.min_color_btn),
            )

            self.max_color_edit = QLineEdit()
            self.max_color_btn = QPushButton("Pick...")
            self.max_color_btn.clicked.connect(
                lambda: self._pick_color(self.max_color_edit)
            )
            form.addRow(
                QLabel("Max gradient color (hex):"),
                self._hbox(self.max_color_edit, self.max_color_btn),
            )

            self.node_color_edit = QLineEdit()
            self.node_color_btn = QPushButton("Pick...")
            self.node_color_btn.clicked.connect(
                lambda: self._pick_color(self.node_color_edit)
            )
            form.addRow(
                QLabel("Default node color (hex):"),
                self._hbox(self.node_color_edit, self.node_color_btn),
            )

            self.text_color_edit = QLineEdit()
            self.text_color_btn = QPushButton("Pick...")
            self.text_color_btn.clicked.connect(
                lambda: self._pick_color(self.text_color_edit)
            )
            form.addRow(
                QLabel("Default text color (hex):"),
                self._hbox(self.text_color_edit, self.text_color_btn),
            )

            layout.addLayout(form)

            box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
            )
            box.accepted.connect(self._on_accept)
            box.rejected.connect(self.reject)
            layout.addWidget(box)

        def _hbox(self, widget, button):
            from PyQt6.QtWidgets import QHBoxLayout, QWidget

            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(0, 0, 0, 0)
            h.addWidget(widget)
            h.addWidget(button)
            return container

        def _pick_color(self, edit: QLineEdit):
            current = edit.text() or "#000000"
            dlg = QColorDialog(self)
            try:
                dlg.setCurrentColor(edit.text())
            except Exception:
                pass
            color = dlg.getColor()
            if color.isValid():
                hexc = color.name()
                edit.setText(hexc)

        def _populate_from_main_window(self):
            try:
                mw = self.main_window
                self.min_color_edit.setText(
                    getattr(mw, "min_gradient_color", mw.default_node_color).name()
                )
            except Exception:
                pass
            try:
                self.max_color_edit.setText(
                    getattr(mw, "max_gradient_color", mw.default_node_color).name()
                )
            except Exception:
                pass
            try:
                self.node_color_edit.setText(
                    getattr(mw, "default_node_color", mw.default_node_color).name()
                )
            except Exception:
                pass
            try:
                self.text_color_edit.setText(
                    getattr(mw, "default_text_color", mw.default_text_color).name()
                )
            except Exception:
                pass

        def _on_accept(self):
            mw = self.main_window
            try:
                mw.min_gradient_color = self._to_qcolor(self.min_color_edit.text())
            except Exception:
                pass
            try:
                mw.max_gradient_color = self._to_qcolor(self.max_color_edit.text())
            except Exception:
                pass
            try:
                mw.default_node_color = self._to_qcolor(self.node_color_edit.text())
            except Exception:
                pass
            try:
                mw.default_text_color = self._to_qcolor(self.text_color_edit.text())
            except Exception:
                pass

            # Try to persist via theme manager if available
            try:
                from .theme import get_theme_manager

                tm = get_theme_manager()
                tm.settings.setValue(
                    "visualization/min_gradient_color", mw.min_gradient_color.name()
                )
                tm.settings.setValue(
                    "visualization/max_gradient_color", mw.max_gradient_color.name()
                )
                tm.settings.setValue(
                    "visualization/default_node_color", mw.default_node_color.name()
                )
                tm.settings.setValue(
                    "visualization/default_text_color", mw.default_text_color.name()
                )
                try:
                    tm.apply_theme()
                except Exception:
                    pass
            except Exception:
                pass

            self.accept()

        def _to_qcolor(self, v: str):
            from PyQt6.QtGui import QColor

            try:
                if not v:
                    return QColor("#000000")
                return QColor(v)
            except Exception:
                return QColor("#000000")
