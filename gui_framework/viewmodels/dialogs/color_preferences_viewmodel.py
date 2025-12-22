"""ViewModel for Color Preferences dialog (theme manager wrapper)."""

from typing import Dict

from ComputationalGraphs.GUI.theme import get_theme_manager
from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class ColorPreferencesViewModel(BaseViewModel):
    """Encapsulates theme changes and exposes convenience methods for views.

    The VM keeps a local copy of the theme map in `self.theme` and applies
    changes to the shared ThemeManager when requested.
    """

    theme_changed = ObservableProperty("theme_changed", default=0)

    def __init__(self):
        super().__init__()
        self.tm = get_theme_manager()
        # Local working copy
        self.theme: Dict[str, str] = dict(self.tm.theme)
        # Subscribe to theme manager changes to keep synchronized
        try:
            self.tm.theme_changed.connect(self._on_external_theme_change)
        except Exception:
            pass

    def initialize(self):
        self._mark_initialized()

    def cleanup(self):
        try:
            # Disconnect if possible
            self.tm.theme_changed.disconnect(self._on_external_theme_change)
        except Exception:
            pass

    def _on_external_theme_change(self):
        # Update local copy and notify observers
        try:
            self.theme = dict(self.tm.theme)
            self.theme_changed += 1
        except Exception:
            pass

    def load_values(self) -> Dict[str, str]:
        # Refresh and return a local copy
        self.theme = dict(self.tm.theme)
        return dict(self.theme)

    def get_color(self, key: str) -> str:
        return self.theme.get(key, self.tm.defaults.get(key, "#000000"))

    def set_color_for_key(self, key: str, hex_color: str, apply_theme: bool = True):
        # Update local map with merged keys semantics similar to ThemeManager
        if key == "panel_bg":
            self.theme["panel_bg"] = hex_color
            self.theme["bg"] = hex_color
            self.theme["dock_bg"] = hex_color
            self.theme["list_bg"] = hex_color
        else:
            self.theme[key] = hex_color

        # Propagate to ThemeManager for preview if requested
        if apply_theme:
            try:
                self.tm.set_theme(self.theme, persist=False)
                self.tm.apply_theme()
                self.theme_changed += 1
            except Exception:
                pass

    def set_font(self, prefix: str, font, persist: bool = False):
        try:
            self.tm.set_font(prefix, font, persist=persist)
            # Update local map
            self.theme.update(self.tm.theme)
            self.theme_changed += 1
        except Exception:
            pass

    def on_apply(self):
        try:
            # Ensure merged keys synced
            if "panel_bg" in self.theme:
                self.theme["bg"] = self.theme["panel_bg"]
            elif "bg" in self.theme:
                self.theme["panel_bg"] = self.theme["bg"]
            self.tm.set_theme(self.theme, persist=False)
            self.tm.apply_theme()
            self.theme_changed += 1
        except Exception:
            pass

    def on_save(self):
        try:
            if "panel_bg" in self.theme:
                self.theme["bg"] = self.theme["panel_bg"]
            elif "bg" in self.theme:
                self.theme["panel_bg"] = self.theme["bg"]
            self.tm.set_theme(self.theme, persist=True)
            self.tm.apply_theme()
            self.theme_changed += 1
        except Exception:
            pass

    def on_reset(self):
        try:
            self.theme = dict(self.tm.defaults)
            # Apply defaults immediately
            self.tm.set_theme(self.theme, persist=False)
            self.tm.apply_theme()
            self.theme_changed += 1
        except Exception:
            pass

    def create_snapshot(self):
        self._snapshot = dict(self.theme)

    def reset_to_snapshot(self):
        if hasattr(self, "_snapshot"):
            self.theme = dict(self._snapshot)
            self.theme_changed += 1
