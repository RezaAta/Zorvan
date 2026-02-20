"""
Theme Adapter - Bridges legacy ThemeManager with new ThemeViewModel.

This adapter synchronizes theme changes between the legacy ThemeManager
(which uses QSettings for persistence) and the new ThemeViewModel (which
uses StateStore). This enables gradual migration from old to new architecture.

Usage:
    adapter = ThemeAdapter()
    adapter.sync_legacy_to_state_store()  # Initial sync
    adapter.start_bidirectional_sync()     # Enable live sync
"""

import os
import sys
from typing import Optional

# Ensure imports work
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from gui_framework.events.bus import EventType, get_event_bus
from gui_framework.state.store import StateEvent, get_store
from gui_framework.viewmodels.theme_viewmodel import ThemeViewModel
from zorvan.GUI.theme import get_theme_manager


class ThemeAdapter:
    """Adapter to bridge legacy ThemeManager with new ThemeViewModel.

    Provides bidirectional synchronization between:
    - Legacy ThemeManager (QSettings persistence, pyqtSignal notifications)
    - New ThemeViewModel (StateStore persistence, EventBus notifications)

    This enables gradual migration without breaking existing code.
    """

    def __init__(self):
        """Initialize the theme adapter."""
        self._theme_manager = get_theme_manager()
        self._theme_viewmodel = ThemeViewModel()
        self._theme_viewmodel.initialize()
        self._state_store = get_store()
        self._event_bus = get_event_bus()
        self._syncing = False  # Prevent infinite loops

    def sync_legacy_to_state_store(self):
        """Sync current theme from legacy ThemeManager to StateStore.

        This should be called once at application startup to ensure
        the StateStore has the current theme from QSettings.
        """
        if self._syncing:
            return

        self._syncing = True
        try:
            # Get colors from legacy theme
            colors = {}
            for key in self._theme_manager.defaults.keys():
                if (
                    not key.endswith("_font_family")
                    and not key.endswith("_font_size")
                    and not key.endswith("_font_weight")
                ):
                    colors[key] = self._theme_manager.theme.get(
                        key, self._theme_manager.defaults.get(key)
                    )

            # Get fonts from legacy theme
            fonts = {}
            for prefix in ("ui", "node"):
                for suffix in ("_font_family", "_font_size", "_font_weight"):
                    key = f"{prefix}{suffix}"
                    fonts[key] = self._theme_manager.theme.get(
                        key, self._theme_manager.defaults.get(key)
                    )

            # Update ThemeViewModel
            self._theme_viewmodel.colors = colors
            self._theme_viewmodel.fonts = fonts
            self._theme_viewmodel.current_theme = "legacy_synced"

            # Update state store (this will trigger state subscribers)
            self._theme_viewmodel._update_theme_state()

        finally:
            self._syncing = False

    def sync_state_store_to_legacy(self):
        """Sync current theme from StateStore to legacy ThemeManager.

        This updates QSettings with the current theme from StateStore.
        """
        if self._syncing:
            return

        self._syncing = True
        try:
            # Get theme from state store
            state = self._state_store.get_state()
            if not state or not state.theme:
                return

            # Build combined theme dict for legacy manager
            theme = {}
            theme.update(state.theme.colors)
            theme.update(state.theme.fonts)

            # Update legacy theme manager
            self._theme_manager.set_theme(theme, persist=True)

        finally:
            self._syncing = False

    def start_bidirectional_sync(self):
        """Start bidirectional synchronization between legacy and new.

        This sets up listeners so changes in either system are reflected in the other.
        """
        # Listen to legacy ThemeManager changes
        try:
            self._theme_manager.theme_changed.connect(self._on_legacy_theme_changed)
        except Exception:
            pass

        # Listen to new StateStore changes
        self._state_store.subscribe(
            StateEvent.THEME_CHANGED, self._on_state_theme_changed
        )

        # Listen to EventBus theme events
        self._event_bus.subscribe(
            EventType.THEME_COLOR_CHANGED, self._on_theme_color_changed
        )
        self._event_bus.subscribe(
            EventType.THEME_FONT_CHANGED, self._on_theme_font_changed
        )
        self._event_bus.subscribe(EventType.THEME_UPDATED, self._on_theme_updated)

    def stop_bidirectional_sync(self):
        """Stop bidirectional synchronization."""
        # Disconnect from legacy ThemeManager
        try:
            self._theme_manager.theme_changed.disconnect(self._on_legacy_theme_changed)
        except Exception:
            pass

        # Unsubscribe from StateStore
        try:
            self._state_store.unsubscribe(
                StateEvent.THEME_CHANGED, self._on_state_theme_changed
            )
        except Exception:
            pass

        # Unsubscribe from EventBus
        try:
            self._event_bus.unsubscribe(
                EventType.THEME_COLOR_CHANGED, self._on_theme_color_changed
            )
            self._event_bus.unsubscribe(
                EventType.THEME_FONT_CHANGED, self._on_theme_font_changed
            )
            self._event_bus.unsubscribe(EventType.THEME_UPDATED, self._on_theme_updated)
        except Exception:
            pass

    def _on_legacy_theme_changed(self):
        """Handle theme changes from legacy ThemeManager."""
        if not self._syncing:
            self.sync_legacy_to_state_store()

    def _on_state_theme_changed(self, theme_state):
        """Handle theme changes from StateStore."""
        if not self._syncing:
            self.sync_state_store_to_legacy()

    def _on_theme_color_changed(self, event):
        """Handle color change events from EventBus."""
        if not self._syncing:
            self.sync_state_store_to_legacy()

    def _on_theme_font_changed(self, event):
        """Handle font change events from EventBus."""
        if not self._syncing:
            self.sync_state_store_to_legacy()

    def _on_theme_updated(self, event):
        """Handle theme update events from EventBus."""
        if not self._syncing:
            self.sync_state_store_to_legacy()

    @property
    def theme_viewmodel(self) -> ThemeViewModel:
        """Access to the ThemeViewModel."""
        return self._theme_viewmodel

    @property
    def theme_manager(self):
        """Access to the legacy ThemeManager."""
        return self._theme_manager


# Singleton instance
_theme_adapter: Optional[ThemeAdapter] = None


def get_theme_adapter() -> ThemeAdapter:
    """Get or create the singleton ThemeAdapter instance.

    Returns:
        ThemeAdapter singleton instance
    """
    global _theme_adapter
    if _theme_adapter is None:
        _theme_adapter = ThemeAdapter()
    return _theme_adapter
