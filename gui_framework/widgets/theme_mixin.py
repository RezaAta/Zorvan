"""
Updated ThemeMixin that bridges legacy ThemeManager with new MVVM architecture.

This mixin allows widgets to react to theme changes from either:
1. The new StateStore (preferred for new widgets)
2. The legacy ThemeManager (for backward compatibility)

Usage:
    class MyWidget(QWidget, ThemeMixin):
        def __init__(self, parent=None):
            QWidget.__init__(self, parent)
            ThemeMixin.__init__(self, use_state_store=True)  # Use new architecture

        def apply_theme(self):
            # Get theme colors/fonts from self.theme_manager or self.theme_viewmodel
            pass
"""

from __future__ import annotations

from typing import Callable, Optional

try:
    from gui_framework.viewmodels.theme_viewmodel import ThemeViewModel
    from gui_framework.state.store import get_store
    from gui_framework.state.store import StateEvent
    HAS_NEW_FRAMEWORK = True
except ImportError:
    HAS_NEW_FRAMEWORK = False

# Import legacy ThemeManager - try multiple paths for compatibility
get_theme_manager = None
try:
    # Try direct import first (when installed as package)
    from ComputationalGraphs.GUI.theme import get_theme_manager
except ImportError:
    try:
        # Try relative import (when running from repo root)
        import sys
        import os
        # Add parent directory to path if not already there
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from ComputationalGraphs.GUI.theme import get_theme_manager
    except ImportError:
        # Last resort: define a dummy function
        def get_theme_manager():
            """Dummy function when ThemeManager is not available."""
            class DummyManager:
                def __init__(self):
                    self.theme = {}
                def get_color(self, key, fallback="#000000"):
                    return fallback
                @property
                def theme_changed(self):
                    class DummySignal:
                        def connect(self, *args):
                            pass
                        def disconnect(self, *args):
                            pass
                        def emit(self):
                            pass
                    return DummySignal()
            return DummyManager()


class ThemeMixin:
    """Mixin for widgets that should react to theme changes.

    Supports both legacy ThemeManager and new ThemeViewModel/StateStore.

    Usage:
        # Legacy mode (default)
        class MyWidget(QWidget, ThemeMixin):
            def __init__(self, parent=None):
                QWidget.__init__(self, parent)
                ThemeMixin.__init__(self)

        # New MVVM mode
        class MyWidget(QWidget, ThemeMixin):
            def __init__(self, parent=None):
                QWidget.__init__(self, parent)
                ThemeMixin.__init__(self, use_state_store=True)

            def apply_theme(self):
                # Access theme via self.theme_viewmodel
                color = self.theme_viewmodel.get_color("bg")
                # ... apply to widget
    """

    def __init__(self, use_state_store: bool = False) -> None:
        """Initialize ThemeMixin.

        Args:
            use_state_store: If True, use new StateStore/ThemeViewModel architecture.
                           If False, use legacy ThemeManager (default for compatibility).
        """
        self._use_state_store = use_state_store and HAS_NEW_FRAMEWORK
        self._theme_manager = None
        self._theme_viewmodel = None
        self._state_store = None

        if self._use_state_store:
            # New architecture: Use StateStore and ThemeViewModel
            try:
                self._state_store = get_store()
                self._theme_viewmodel = ThemeViewModel()
                self._theme_viewmodel.initialize()

                # Subscribe to state changes
                self._state_store.subscribe(
                    StateEvent.THEME_CHANGED, self._on_theme_state_changed
                )

                # Apply theme immediately
                self._on_theme_changed()
            except Exception:
                # Fall back to legacy if new framework fails
                self._use_state_store = False
                self._setup_legacy()
        else:
            # Legacy architecture: Use ThemeManager
            self._setup_legacy()

    def _setup_legacy(self) -> None:
        """Set up legacy ThemeManager connection."""
        self._theme_manager = get_theme_manager()
        # Keep a reference to avoid GC surprises
        try:
            self._theme_manager.theme_changed.connect(self._on_theme_changed)
        except Exception:
            # In tests or import-time cases the signal may not be present
            pass
        # Apply theme immediately
        self._on_theme_changed()

    def _on_theme_state_changed(self, theme_state) -> None:
        """Handle theme state changes from StateStore."""
        # Reload theme from state
        if self._theme_viewmodel:
            # Update viewmodel from state
            state = self._state_store.get_state()
            if state and state.theme:
                self._theme_viewmodel.colors = dict(state.theme.colors)
                self._theme_viewmodel.fonts = dict(state.theme.fonts)
                self._theme_viewmodel.current_theme = state.theme.current_theme

        # Trigger theme application
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
        """Get legacy ThemeManager instance.

        Returns:
            ThemeManager instance (legacy mode) or None (new mode)
        """
        return self._theme_manager

    @property
    def theme_manager(self):
        """Access to legacy ThemeManager for backward compatibility."""
        return self._theme_manager

    @property
    def theme_viewmodel(self) -> Optional[ThemeViewModel]:
        """Access to new ThemeViewModel (only available in new mode).

        Returns:
            ThemeViewModel instance if using StateStore, None otherwise
        """
        return self._theme_viewmodel

    def disconnect_theme(self):
        """Disconnect theme change signals (useful for cleanup/tests)."""
        if self._use_state_store and self._state_store:
            try:
                self._state_store.unsubscribe(
                    StateEvent.THEME_CHANGED, self._on_theme_state_changed
                )
            except Exception:
                pass
            if self._theme_viewmodel:
                try:
                    self._theme_viewmodel.cleanup()
                except Exception:
                    pass
        elif self._theme_manager:
            try:
                self._theme_manager.theme_changed.disconnect(self._on_theme_changed)
            except Exception:
                pass
