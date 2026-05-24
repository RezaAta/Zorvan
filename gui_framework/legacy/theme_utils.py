"""Utility helpers for theme-aware widgets.

This module provides `ThemeMixin`, a small mixin that connects a widget to
`ThemeManager.theme_changed` and calls `apply_theme()` when the theme changes.
"""

from __future__ import annotations

from typing import Callable

from .theme import get_theme_manager


class ThemeMixin:
    """Mixin for widgets that should react to theme changes.

    Usage:
        class MyWidget(QWidget, ThemeMixin):
            def __init__(self, parent=None):
                QWidget.__init__(self, parent)
                ThemeMixin.__init__(self)

            def apply_theme(self):
                # read colors/fonts from get_theme_manager() and apply
                pass
    """

    def __init__(self) -> None:
        # Obtain manager and connect
        self._theme_manager = get_theme_manager()
        # Keep a reference to avoid GC surprises
        try:
            self._theme_manager.theme_changed.connect(self._on_theme_changed)
        except Exception:
            # In tests or import-time cases the signal may not be present
            pass
        # Apply theme immediately
        self._on_theme_changed()

    def _on_theme_changed(self) -> None:
        """Internal slot invoked when theme changes; calls `apply_theme()`.

        Subclasses should implement `apply_theme()`.
        """
        try:
            self.apply_theme()
        except AttributeError:
            # Subclass hasn't provided apply_theme; ignore
            return
        except Exception:
            # Don't let theme errors propagate and break UI
            return

    def get_theme_manager(self):
        return self._theme_manager

    def disconnect_theme(self):
        """Disconnect the theme_changed signal (useful for cleanup/tests)."""
        try:
            self._theme_manager.theme_changed.disconnect(self._on_theme_changed)
        except Exception:
            pass
