"""MVVM Color Preferences Dialog - binds to ColorPreferencesViewModel."""

try:
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
    )

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

from ...viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from gui_framework.viewmodels.dialogs.color_preferences_viewmodel import (
        ColorPreferencesViewModel,
    )

    from ..base import BaseView

    class ColorPreferencesDialog(QDialog, BaseView):
        def __init__(self, viewmodel: BaseViewModel, parent=None):
            QDialog.__init__(self, parent)
            BaseView.__init__(self, viewmodel, parent)
            self.setWindowTitle("Color Preferences")
            self._vm = viewmodel
            self._setup_ui()
            try:
                self._bind_viewmodel()
            except Exception:
                pass

        def _setup_ui(self):
            self.layout = QVBoxLayout(self)
            form = QFormLayout()

            # Font buttons
            self.ui_font_btn = QPushButton("Select UI Font...")
            self.ui_font_btn.clicked.connect(lambda: self._choose_font("ui"))
            form.addRow(QLabel("UI Font"), self.ui_font_btn)

            self.node_font_btn = QPushButton("Select Node Font...")
            self.node_font_btn.clicked.connect(lambda: self._choose_font("node"))
            form.addRow(QLabel("Node Font"), self.node_font_btn)

            # Color keys
            self.buttons = {}
            keys = [
                ("panel_bg", "Panel Background"),
                ("canvas_bg", "Canvas Background"),
                ("grid_color", "Grid Color"),
                ("edge_color", "Edge Color"),
                ("header_bg", "Header Color"),
                ("node_default", "Default Node Color"),
                ("node_text", "Default Node Text Color"),
                ("text", "Global Text Color"),
                ("accent", "Accent / Highlight"),
            ]
            for key, label in keys:
                btn = QPushButton()
                btn.setFixedWidth(80)
                btn.clicked.connect(lambda _, k=key: self._choose_color(k))
                self.buttons[key] = btn
                form.addRow(QLabel(label), btn)

            self.layout.addLayout(form)

            # Action buttons
            hb = QHBoxLayout()
            self.apply_btn = QPushButton("Apply")
            self.save_btn = QPushButton("Save as Default")
            self.reset_btn = QPushButton("Reset to Defaults")

            self.apply_btn.clicked.connect(lambda: self.get_viewmodel().on_apply())
            self.save_btn.clicked.connect(lambda: self.get_viewmodel().on_save())
            self.reset_btn.clicked.connect(lambda: self.get_viewmodel().on_reset())

            hb.addWidget(self.apply_btn)
            hb.addWidget(self.save_btn)
            hb.addWidget(self.reset_btn)
            self.layout.addLayout(hb)

            bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            bb.rejected.connect(self.reject)
            self.layout.addWidget(bb)

            # Initial render
            self._render_from_vm()

        def _bind_viewmodel(self):
            vm: ColorPreferencesViewModel = self.get_viewmodel()
            vm.observe_property("theme_changed", lambda o, n: self._render_from_vm())

        def _render_from_vm(self):
            vm: ColorPreferencesViewModel = self.get_viewmodel()
            try:
                vm.create_snapshot()
            except Exception:
                pass
            # Fill buttons with current colors
            for k, btn in self.buttons.items():
                try:
                    hexcol = vm.get_color(k)
                    btn.setStyleSheet(f"background: {hexcol}")
                except Exception:
                    pass

        def _choose_color(self, key: str):
            # Interactive color dialog – for tests we prefer calling viewmodel directly
            from PyQt6.QtWidgets import QColorDialog

            current = QColor(self.get_viewmodel().get_color(key))
            c = QColorDialog.getColor(current, self, f"Choose {key}")
            if c.isValid():
                self.get_viewmodel().set_color_for_key(key, c.name(), apply_theme=True)

        def _choose_font(self, prefix: str):
            from PyQt6.QtWidgets import QFontDialog

            # Let the ThemeManager build a current font; request new one
            current_font = None
            try:
                current_font = self.get_viewmodel().tm.get_font(prefix)
            except Exception:
                pass
            font, ok = QFontDialog.getFont(current_font, self, f"Choose {prefix} font")
            if ok and font:
                self.get_viewmodel().set_font(prefix, font, persist=False)

else:

    class ColorPreferencesDialog:
        def __init__(self, vm, parent=None):
            self.viewmodel = vm

        def exec(self):
            return 0
