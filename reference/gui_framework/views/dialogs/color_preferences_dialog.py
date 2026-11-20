"""MVVM Color Preferences Dialog - binds to ColorPreferencesViewModel."""

try:
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QMessageBox,
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

            # Theme selection (Saved/Named themes)
            theme_h = QHBoxLayout()
            self.theme_label = QLabel("Selected Theme")
            self.theme_combo = QComboBox()
            self.save_theme_btn = QPushButton("Save Theme...")
            self.delete_theme_btn = QPushButton("Delete Theme")
            self.set_selected_btn = QPushButton("Set as Selected")
            self.save_theme_btn.clicked.connect(lambda: self._on_save_theme_clicked())
            self.delete_theme_btn.clicked.connect(
                lambda: self._on_delete_theme_clicked()
            )
            self.set_selected_btn.clicked.connect(
                lambda: self._on_set_selected_theme_clicked()
            )
            self.theme_combo.currentTextChanged.connect(
                lambda name: self._on_theme_selected(name)
            )
            theme_h.addWidget(self.theme_label)
            theme_h.addWidget(self.theme_combo)
            theme_h.addWidget(self.save_theme_btn)
            theme_h.addWidget(self.delete_theme_btn)
            theme_h.addWidget(self.set_selected_btn)
            self.layout.addLayout(theme_h)

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
            vm.observe_property(
                "themes_changed", lambda o, n: self._populate_theme_combo()
            )
            # Populate available named themes initially
            try:
                self._populate_theme_combo()
            except Exception:
                pass

        def reject(self):
            # Ensure viewmodel cleanup and safe teardown to avoid lingering Qt
            # objects that may be processed asynchronously by the event loop.
            try:
                vm: ColorPreferencesViewModel = self.get_viewmodel()
                try:
                    vm.cleanup()
                except Exception:
                    pass
            except Exception:
                pass
            try:
                super().reject()
            except Exception:
                pass
            try:
                self.setParent(None)
                self.deleteLater()
                import gc

                gc.collect()
                from PyQt6.QtWidgets import QApplication

                app = QApplication.instance()
                if app is not None:
                    app.processEvents()
            except Exception:
                pass

        def close(self):
            # Mirror reject behavior when closed programmatically
            try:
                vm: ColorPreferencesViewModel = self.get_viewmodel()
                try:
                    vm.cleanup()
                except Exception:
                    pass
            except Exception:
                pass
            try:
                super().close()
            except Exception:
                pass
            try:
                self.setParent(None)
                self.deleteLater()
                import gc

                gc.collect()
                from PyQt6.QtWidgets import QApplication

                app = QApplication.instance()
                if app is not None:
                    app.processEvents()
            except Exception:
                pass

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

        def _populate_theme_combo(self):
            vm = self.get_viewmodel()
            try:
                names = vm.get_named_themes()
            except Exception:
                names = []
            try:
                self.theme_combo.blockSignals(True)
            except Exception:
                pass
            try:
                self.theme_combo.clear()
            except Exception:
                pass
            try:
                self.theme_combo.addItems(names)
            except Exception:
                pass
            try:
                selected = vm.get_selected_theme_name()
                if selected and selected in names:
                    idx = self.theme_combo.findText(selected)
                    if idx >= 0:
                        self.theme_combo.setCurrentIndex(idx)
            except Exception:
                pass
            try:
                self.theme_combo.blockSignals(False)
            except Exception:
                pass

        def _on_theme_selected(self, name: str):
            if not name:
                return
            try:
                self.get_viewmodel().apply_named_theme(name, persist=False)
                # Re-render colors from VM
                self._render_from_vm()
            except Exception:
                pass

        def _on_save_theme_clicked(self):
            vm = self.get_viewmodel()
            try:
                name, ok = QInputDialog.getText(self, "Save Theme", "Theme name:")
                if ok and name:
                    vm.save_named_theme(str(name))
                    try:
                        self._populate_theme_combo()
                    except Exception:
                        pass
            except Exception:
                pass

        def _on_delete_theme_clicked(self):
            try:
                name = self.theme_combo.currentText()
                if not name:
                    return
                reply = QMessageBox.question(
                    self,
                    "Delete Theme",
                    f"Delete theme '{name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.get_viewmodel().delete_named_theme(name)
                    try:
                        self._populate_theme_combo()
                    except Exception:
                        pass
            except Exception:
                pass

        def _on_set_selected_theme_clicked(self):
            try:
                name = self.theme_combo.currentText()
                if not name:
                    return
                self.get_viewmodel().set_selected_theme_name(name, persist=True)
                QMessageBox.information(
                    self, "Selected", f"Theme '{name}' set as selected."
                )
            except Exception:
                pass

else:

    class ColorPreferencesDialog:
        def __init__(self, vm, parent=None):
            self.viewmodel = vm

        def exec(self):
            return 0
