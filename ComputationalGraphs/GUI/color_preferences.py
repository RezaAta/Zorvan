"""Color / Theme preferences dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .theme import get_theme_manager


class ColorPreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Color Preferences")
        self.tm = get_theme_manager()
        self._original_theme = dict(self.tm.theme)
        self.theme = dict(self._original_theme)
        # Track whether user applied changes (so we don't revert on close)
        self._applied = False

        self.layout = QVBoxLayout(self)

        form = QFormLayout()

        # Font pickers
        from PyQt6.QtWidgets import QFontDialog

        self.ui_font_btn = QPushButton("Select UI Font...")
        self.ui_font_btn.clicked.connect(lambda: self.choose_font("ui"))
        form.addRow(QLabel("UI Font"), self.ui_font_btn)

        self.node_font_btn = QPushButton("Select Node Font...")
        self.node_font_btn.clicked.connect(lambda: self.choose_font("node"))
        form.addRow(QLabel("Node Font"), self.node_font_btn)

        # Create simple color pickers for a few keys
        self.buttons: dict[str, QPushButton] = {}

        # Use a single 'Panel Background' control to drive all panel/dock/list backgrounds
        for key, label in [
            ("panel_bg", "Panel Background (panels, docks, palettes)"),
            ("canvas_bg", "Canvas Background"),
            ("grid_color", "Grid Color"),
            ("edge_color", "Edge Color"),
            ("header_bg", "Header Color (Menus / Toolbar)"),
            ("node_default", "Default Node Color"),
            ("node_text", "Default Node Text Color"),
            ("text", "Global Text Color"),
            ("accent", "Accent / Highlight"),
        ]:
            btn = QPushButton()
            btn.setFixedWidth(80)
            btn.clicked.connect(lambda _, k=key: self.choose_color(k))
            self.buttons[key] = btn
            form.addRow(QLabel(label), btn)

        self.layout.addLayout(form)

        # Buttons
        hb = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.save_btn = QPushButton("Save as Default")
        self.reset_btn = QPushButton("Reset to Defaults")

        self.apply_btn.clicked.connect(self.on_apply)
        self.save_btn.clicked.connect(self.on_save)
        self.reset_btn.clicked.connect(self.on_reset)

        hb.addWidget(self.apply_btn)
        hb.addWidget(self.save_btn)
        hb.addWidget(self.reset_btn)

        self.layout.addLayout(hb)

        # Dialog button box for close
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject)
        self.layout.addWidget(bb)

        self.load_values()

    def choose_font(self, prefix: str):
        """Open a font dialog and apply the chosen font for 'ui' or 'node'."""
        from PyQt6.QtWidgets import QFontDialog

        current_font = None
        try:
            if prefix == "ui":
                current_font = self.tm.get_font("ui")
            else:
                current_font = self.tm.get_font("node")
        except Exception:
            pass

        font, ok = QFontDialog.getFont(current_font, self, f"Choose {prefix} font")
        if ok and font:
            try:
                # Apply immediately (don't persist until Save)
                self.tm.set_font(prefix, font, persist=False)
                # Also update the dialog-local theme map so Apply will use the
                # newly chosen font values even if the user hasn't clicked Save.
                try:
                    self.theme[f"{prefix}_font_family"] = font.family()
                    self.theme[f"{prefix}_font_size"] = str(font.pointSize())
                    # Try to reuse any friendly weight name that tm.set_font stored;
                    # fall back to a numeric->name map if needed
                    weight_name = self.tm.theme.get(f"{prefix}_font_weight", None)
                    if weight_name is None:
                        wmap_rev = {
                            100: "Thin",
                            200: "Extra-Light",
                            250: "Extra-Light",
                            300: "Light",
                            400: "Normal",
                            500: "Medium",
                            600: "DemiBold",
                            700: "Bold",
                            800: "Black",
                        }
                        weight_name = wmap_rev.get(font.weight(), None)
                    if weight_name:
                        self.theme[f"{prefix}_font_weight"] = weight_name
                    self.theme[f"{prefix}_font_italic"] = bool(font.italic())
                except Exception:
                    pass
                # Refresh the dialog controls to reflect the new font selection
                try:
                    self.load_values()
                except Exception:
                    pass
                # For UI font, apply to QApplication immediately
                try:
                    from PyQt6.QtWidgets import QApplication

                    # Set application font on the QApplication instance and reapply stylesheet
                    try:
                        app = QApplication.instance()
                        if app is not None:
                            app.setFont(self.tm.get_font("ui"))
                    except Exception:
                        pass

                    # Reapply theme stylesheet (fonts may be used by stylesheet placeholders)
                    try:
                        self.tm.apply_theme()
                    except Exception:
                        pass
                except Exception:
                    # If setting the QApplication font or applying theme failed, ignore
                    pass
                # Notify listeners
                self.tm.theme_changed.emit()
                # Mark as applied so dialog close doesn't revert
                self._applied = True
            except Exception:
                pass

    def reject(self) -> None:
        """Restore original theme only if user did not apply changes during this dialog.

        If the user clicked Apply or Save, we keep the applied changes when closing.
        """
        try:
            if not getattr(self, "_applied", False):
                # Revert to original theme (non-persistent)
                self.tm.set_theme(self._original_theme, persist=False)
                self.tm.apply_theme()
        except Exception:
            pass
        super().reject()

    def load_values(self):
        # Ensure merged keys: prefer panel_bg over bg for historic compatibility
        if "panel_bg" not in self.theme and "bg" in self.theme:
            self.theme["panel_bg"] = self.theme["bg"]
        if "bg" not in self.theme and "panel_bg" in self.theme:
            self.theme["bg"] = self.theme["panel_bg"]

        # Prefer theme manager defaults if values missing
        for k, btn in self.buttons.items():
            hexcol = self.theme.get(k, None)
            if hexcol is None:
                hexcol = self.tm.defaults.get(k, "#000000")
            btn.setStyleSheet(f"background: {hexcol}")

        # Update font button labels to show current selections
        try:
            ui_font = self.tm.get_font("ui")
            # Show family, size and weight name
            wmap = {
                100: "Thin",
                200: "Extra-Light",
                250: "Extra-Light",
                300: "Light",
                400: "Normal",
                500: "Medium",
                600: "DemiBold",
                700: "Bold",
                800: "Black",
            }
            weight_name = wmap.get(ui_font.weight(), "")
            self.ui_font_btn.setText(
                f"UI Font: {ui_font.family()} {ui_font.pointSize()}pt {weight_name}"
            )
        except Exception:
            pass
        try:
            node_font = self.tm.get_font("node")
            weight_name = wmap.get(node_font.weight(), "")
            self.node_font_btn.setText(
                f"Node Font: {node_font.family()} {node_font.pointSize()}pt {weight_name}"
            )
        except Exception:
            pass

    def choose_color(self, key: str):
        """Open color dialog for a key and apply the color immediately."""
        current = QColor(self.theme.get(key, "#000000"))
        c = QColorDialog.getColor(current, self, f"Choose {key}")
        if c.isValid():
            self.set_color_for_key(key, c.name())

    def set_color_for_key(self, key: str, hex_color: str, apply_theme: bool = True):
        """Programmatic helper to set a color for a key (used by tests).

        If apply_theme=True, the change is applied immediately (preview).
        For panel_bg, also sync dock_bg and list_bg so panels/docks follow the single attribute.
        """
        if key == "panel_bg":
            # Panel background is authoritative; keep bg for legacy keys in sync
            self.theme["panel_bg"] = hex_color
            self.theme["bg"] = hex_color
            # Also set derived keys explicitly for immediate consistency
            self.theme["dock_bg"] = hex_color
            self.theme["list_bg"] = hex_color
        else:
            self.theme[key] = hex_color

        if key in self.buttons:
            try:
                self.buttons[key].setStyleSheet(f"background: {hex_color}")
            except Exception:
                pass

        if apply_theme:
            try:
                # Keep merged keys synced for immediate preview
                if "panel_bg" in self.theme:
                    self.theme["bg"] = self.theme["panel_bg"]
                    self.theme["dock_bg"] = self.theme["panel_bg"]
                    self.theme["list_bg"] = self.theme["panel_bg"]
                elif "bg" in self.theme:
                    self.theme["panel_bg"] = self.theme["bg"]
                self.tm.set_theme(self.theme, persist=False)
                self.tm.apply_theme()
                # Force icon reapply handlers to run immediately so icons update in tests
                try:
                    from .controllers.control_panel_builder import (
                        _ICON_REAPPLY_HANDLERS,
                    )

                    for h in _ICON_REAPPLY_HANDLERS:
                        try:
                            h()
                        except Exception:
                            pass
                except Exception:
                    pass
                # Also emit theme_changed to trigger any handlers connected via signals
                try:
                    self.tm.theme_changed.emit()
                except Exception:
                    pass
                # Ensure event loop processes pending painting and stylesheet updates
                try:
                    from PyQt6.QtWidgets import QApplication

                    app = QApplication.instance()
                    if app is not None:
                        app.processEvents()
                except Exception:
                    pass
                # If dialog has a parent MainWindow, ask it to refresh dock backgrounds
                try:
                    parent = self.parent()
                    if parent is not None and hasattr(
                        parent, "refresh_dock_backgrounds"
                    ):
                        try:
                            parent.refresh_dock_backgrounds()
                        except Exception:
                            pass
                except Exception:
                    pass
                self._applied = True
            except Exception:
                pass

    def on_apply(self):
        # Ensure merged keys stay synced
        if "panel_bg" in self.theme:
            self.theme["bg"] = self.theme["panel_bg"]
        elif "bg" in self.theme:
            self.theme["panel_bg"] = self.theme["bg"]
        # Apply without persisting (real-time preview)
        try:
            self.tm.set_theme(self.theme, persist=False)
            # Ensure fonts selected in the dialog also apply even when not saving
            try:
                self.tm.set_font("ui", self.tm.get_font("ui"), persist=False)
                self.tm.set_font("node", self.tm.get_font("node"), persist=False)
            except Exception:
                pass
            self.tm.apply_theme()
            # Mark as applied so dialog close doesn't revert
            self._applied = True
        except Exception:
            pass

    def on_save(self):
        # Ensure merged keys stay synced and persist
        if "panel_bg" in self.theme:
            self.theme["bg"] = self.theme["panel_bg"]
        elif "bg" in self.theme:
            self.theme["panel_bg"] = self.theme["bg"]
        try:
            self.tm.set_theme(self.theme, persist=True)
            # Persist fonts as well
            try:
                self.tm.set_font("ui", self.tm.get_font("ui"), persist=True)
                self.tm.set_font("node", self.tm.get_font("node"), persist=True)
            except Exception:
                pass
            self.tm.apply_theme()
            # Mark as applied (persisted)
            self._applied = True
        except Exception:
            pass

    def on_reset(self):
        self.theme = dict(self.tm.defaults)
        self.load_values()
        self.on_apply()
