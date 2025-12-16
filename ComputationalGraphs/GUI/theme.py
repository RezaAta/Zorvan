"""Theme manager for GUI colors and stylesheet application."""

from __future__ import annotations

import json
import os
from typing import Dict, List

from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication


class ThemeManager(QObject):
    """Singleton manager handling theme values, persistence and application."""

    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = QSettings("ComputationalGraphs", "GUI")
        self.defaults = {
            "bg": "#2b2b2b",
            "panel_bg": "#3c3f41",
            "dock_bg": "#3c3f41",
            "canvas_bg": "#232526",
            "header_bg": "#239483",
            "text": "#bbbbbb",
            "list_bg": "#313335",
            "accent": "#4a86e8",
            "button_bg": "#4a4a4a",
            "button_hover": "#5a5a5a",
            "button_pressed": "#3a3a3a",
            "button_disabled_bg": "#333333",
            "muted_text": "#666666",
            "border": "#555555",
            "grid_color": "#4a4a4a",
            "edge_color": "#505050",
            "node_default": "#003fbd",
            "node_text": "#ffffff",
            # Font defaults (family, point size, and weight)
            "ui_font_family": "Oswald",
            "ui_font_size": "12",
            "ui_font_weight": "Medium",
            "node_font_family": "Oswald",
            "node_font_size": "10",
            "node_font_weight": "Medium",
        }
        self.theme = self.load_theme()
        # If the user hasn't selected a UI font yet, apply the new default (Oswald Medium 12)
        try:
            if not self.settings.contains("font/ui_family"):
                from PyQt6.QtGui import QFont
                from PyQt6.QtGui import QFont as _QFont

                f = QFont("Oswald", 12)
                try:
                    f.setWeight(_QFont.Weight.Medium)
                    if _QFont.Weight.Medium >= _QFont.Weight.Bold:
                        f.setBold(True)
                except Exception:
                    pass
                app = QApplication.instance()
                if app is not None:
                    app.setFont(f)
            else:
                app = QApplication.instance()
                if app is not None:
                    app.setFont(self.get_font("ui"))
        except Exception:
            pass

    def load_theme(self) -> Dict[str, str]:
        theme = dict(self.defaults)
        try:
            for k in self.defaults.keys():
                v = self.settings.value(f"theme/{k}", None)
                if v:
                    theme[k] = v
            # Also load fonts if stored under font/* keys
            for prefix in ("ui", "node"):
                fam = self.settings.value(f"font/{prefix}_family", None)
                size = self.settings.value(f"font/{prefix}_size", None)
                weight = self.settings.value(f"font/{prefix}_weight", None)
                if fam:
                    theme[f"{prefix}_font_family"] = fam
                if size:
                    theme[f"{prefix}_font_size"] = str(size)
                if weight:
                    theme[f"{prefix}_font_weight"] = str(weight)
                italic = self.settings.value(f"font/{prefix}_italic", None)
                if italic is not None:
                    # QSettings may store booleans as 'true'/'false' strings depending on backend
                    if isinstance(italic, str):
                        theme[f"{prefix}_font_italic"] = italic.lower() in (
                            "1",
                            "true",
                            "yes",
                        )
                    else:
                        theme[f"{prefix}_font_italic"] = bool(italic)
        except Exception:
            pass
        return theme

    def save_theme(self, theme: Dict[str, str]):
        try:
            for k, v in theme.items():
                self.settings.setValue(f"theme/{k}", v)
            self.theme = dict(theme)
            # Persist and notify listeners
            self.theme_changed.emit()
        except Exception:
            pass

    def set_theme(self, theme: Dict[str, str], persist: bool = False):
        """Set theme temporarily (or persist if requested) and notify listeners.

        Keep 'bg' and 'panel_bg' in sync so a single control can drive both.
        """
        t = dict(theme)
        if "panel_bg" in t and "bg" not in t:
            t["bg"] = t["panel_bg"]
        if "bg" in t and "panel_bg" not in t:
            t["panel_bg"] = t["bg"]
        self.theme = t
        if persist:
            self.save_theme(self.theme)
        else:
            # notify listeners so UI can update even if not saved
            self.theme_changed.emit()

    def get_color(self, key: str, fallback: str = "#000000"):
        v = self.theme.get(key, None)
        if v is None:
            v = self.defaults.get(key, fallback)
        try:
            return QColor(v)
        except Exception:
            return QColor(fallback)

    def get_font(self, prefix: str):
        """Return a QFont built from theme settings for the given prefix ('ui' or 'node')."""
        from PyQt6.QtGui import QFont

        family = self.theme.get(f"{prefix}_font_family", None)
        size = self.theme.get(f"{prefix}_font_size", None)
        weight = self.theme.get(f"{prefix}_font_weight", None)
        if family is None:
            # Fallback to defaults stored under keys
            family = self.theme.get(f"{prefix}_font_family", None) or self.defaults.get(
                f"{prefix}_font_family", "Segoe UI"
            )
        if size is None:
            size = self.theme.get(f"{prefix}_font_size", None) or self.defaults.get(
                f"{prefix}_font_size", "10"
            )
        if weight is None:
            weight = self.theme.get(f"{prefix}_font_weight", None) or self.defaults.get(
                f"{prefix}_font_weight", "Normal"
            )

        # Check for italic flag in theme map
        italic_flag = self.theme.get(f"{prefix}_font_italic", None)

        try:
            f = QFont(family, int(size))
            # Map weight strings to QFont.Weight
            wstr = str(weight).lower()
            from PyQt6.QtGui import QFont as _QFont

            wmap = {
                "thin": _QFont.Weight.Thin,
                "extra-light": _QFont.Weight.ExtraLight,
                "light": _QFont.Weight.Light,
                "normal": _QFont.Weight.Normal,
                "medium": _QFont.Weight.Medium,
                "demibold": _QFont.Weight.DemiBold,
                "bold": _QFont.Weight.Bold,
                "black": _QFont.Weight.Black,
            }
            qw = wmap.get(wstr, _QFont.Weight.Normal)
            try:
                f.setWeight(qw)
                if qw >= _QFont.Weight.Bold:
                    f.setBold(True)
            except Exception:
                pass

            # Apply italic if requested
            try:
                if italic_flag is not None:
                    f.setItalic(bool(italic_flag))
            except Exception:
                pass

            return f
        except Exception:
            return QFont("Segoe UI", 10)

    def set_font(self, prefix: str, font, persist: bool = False):
        """Set font family, size & weight for the given prefix and optionally persist."""
        try:
            # Accept either QFont or (family, size, weight)
            if hasattr(font, "family"):
                family = font.family()
                size = font.pointSize()
                try:
                    weight_val = font.weight()
                except Exception:
                    weight_val = None
            elif isinstance(font, (list, tuple)):
                family, size = font[0], int(font[1])
                weight_val = font[2] if len(font) > 2 else None
            else:
                return

            # Map numeric weight to a friendly name if needed
            weight_name = None
            try:
                if weight_val is not None:
                    from PyQt6.QtGui import QFont as _QFont

                    wmap_rev = {
                        _QFont.Weight.Thin: "Thin",
                        _QFont.Weight.ExtraLight: "Extra-Light",
                        _QFont.Weight.Light: "Light",
                        _QFont.Weight.Normal: "Normal",
                        _QFont.Weight.Medium: "Medium",
                        _QFont.Weight.DemiBold: "DemiBold",
                        _QFont.Weight.Bold: "Bold",
                        _QFont.Weight.Black: "Black",
                    }
                    weight_name = wmap_rev.get(weight_val, str(weight_val))
            except Exception:
                pass

            # Save in QSettings for persistence
            self.settings.setValue(f"font/{prefix}_family", family)
            self.settings.setValue(f"font/{prefix}_size", int(size))
            if weight_name is not None:
                self.settings.setValue(f"font/{prefix}_weight", weight_name)
            # Save italic state if available
            try:
                italic_val = False
                if hasattr(font, "italic"):
                    italic_val = bool(font.italic())
                elif isinstance(font, (list, tuple)) and len(font) > 3:
                    italic_val = bool(font[3])
                self.settings.setValue(f"font/{prefix}_italic", bool(italic_val))
                # Keep italic flag in the in-memory theme map as well
                self.theme[f"{prefix}_font_italic"] = bool(italic_val)
            except Exception:
                pass

            # Also keep in-memory theme map for convenience
            self.theme[f"{prefix}_font_family"] = family
            self.theme[f"{prefix}_font_size"] = str(size)
            if weight_name is not None:
                self.theme[f"{prefix}_font_weight"] = weight_name

            if persist:
                # Persist theme (which includes fonts keys)
                self.save_theme(self.theme)
            else:
                self.theme_changed.emit()
        except Exception:
            pass

    def apply_theme(self, app: QApplication | None = None) -> bool:
        """Apply stylesheet by filling template placeholders.

        Returns True if applied, False otherwise.
        """
        base_dir = os.path.dirname(__file__)
        template_path = os.path.join(base_dir, "styles_template.qss")
        fallback_path = os.path.join(base_dir, "styles.qss")

        try:
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    s = f.read()
                for k, v in self.theme.items():
                    s = s.replace("{{%s}}" % k, v)
                if app is None:
                    app = QApplication.instance()
                if app is not None:
                    app.setStyleSheet(s)
                    # Apply UI font if available
                    try:
                        ui_font = self.get_font("ui")
                        app.setFont(ui_font)
                    except Exception:
                        pass
                    self.theme_changed.emit()
                    return True
                return False
            elif os.path.exists(fallback_path):
                with open(fallback_path, "r", encoding="utf-8") as f:
                    s = f.read()
                if app is None:
                    app = QApplication.instance()
                if app is not None:
                    app.setStyleSheet(s)
                    # Apply UI font if available
                    try:
                        ui_font = self.get_font("ui")
                        app.setFont(ui_font)
                    except Exception:
                        pass
                    self.theme_changed.emit()
                    return True
        except Exception:
            pass
        return False


# Module-level singleton
_manager: ThemeManager | None = None


def get_theme_manager() -> ThemeManager:
    global _manager
    if _manager is None:
        _manager = ThemeManager()
    return _manager
