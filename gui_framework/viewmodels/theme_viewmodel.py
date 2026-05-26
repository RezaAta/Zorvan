"""
Theme ViewModel - Pure Python logic for theme management.

Manages theme colors, fonts, and persistence using StateStore.
This ViewModel is completely testable without PyQt dependencies.
"""

from typing import Dict, Optional

from ..events.bus import Event, EventType
from ..state.models import ThemeState
from ..viewmodels.base import BaseViewModel, ObservableProperty


class ThemeViewModel(BaseViewModel):
    """ViewModel for theme management.

    Pure Python logic with no PyQt dependencies. Manages theme colors,
    fonts, and provides methods for theme updates and persistence.

    Attributes:
        colors: Dictionary of color name to hex color value
        fonts: Dictionary of font name to font configuration
        current_theme: Name of current theme
    """

    # Observable properties
    colors = ObservableProperty("colors", default={})
    fonts = ObservableProperty("fonts", default={})
    current_theme = ObservableProperty("current_theme", default="default")

    # Default theme values
    DEFAULT_COLORS = {
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
    }

    DEFAULT_FONTS = {
        "ui_font_family": "Oswald",
        "ui_font_size": "12",
        "ui_font_weight": "Medium",
        "node_font_family": "Oswald",
        "node_font_size": "10",
        "node_font_weight": "Medium",
    }

    def __init__(self, **kwargs):
        """Initialize ThemeViewModel.

        Args:
            **kwargs: Forward compatibility for additional init args
        """
        super().__init__()

        # Initialize with default theme
        self.colors = dict(self.DEFAULT_COLORS)
        self.fonts = dict(self.DEFAULT_FONTS)
        self.current_theme = "default"

    def initialize(self):
        """Initialize the theme ViewModel.

        Load theme from state store and subscribe to events.
        """
        # Load theme from state store
        state = self._store.get_state()
        if state and state.theme:
            theme_state = state.theme
            if theme_state.colors:
                self.colors = dict(theme_state.colors)
            if theme_state.fonts:
                self.fonts = dict(theme_state.fonts)
            if theme_state.current_theme:
                self.current_theme = theme_state.current_theme

    def cleanup(self):
        """Clean up resources."""
        pass

    def get_color(self, key: str, fallback: str = "#000000") -> str:
        """Get a color value by key.

        Args:
            key: Color key (e.g., "bg", "text", "accent")
            fallback: Fallback color if key not found

        Returns:
            Hex color string
        """
        return self.colors.get(key, self.DEFAULT_COLORS.get(key, fallback))

    def set_color(self, key: str, value: str):
        """Set a color value.

        Args:
            key: Color key
            value: Hex color string
        """
        # Create new dict to trigger property change
        new_colors = dict(self.colors)
        new_colors[key] = value
        self.colors = new_colors

        # Update state store
        self._update_theme_state()

        # Publish event
        self._event_bus.publish(
            Event(
                type=EventType.THEME_COLOR_CHANGED,
                payload={"color_changed": key, "value": value},
            )
        )

    def get_font(self, prefix: str) -> Dict[str, str]:
        """Get font configuration for a prefix.

        Args:
            prefix: Font prefix ("ui" or "node")

        Returns:
            Dictionary with family, size, weight keys
        """
        return {
            "family": self.fonts.get(
                f"{prefix}_font_family",
                self.DEFAULT_FONTS.get(f"{prefix}_font_family", "Oswald"),
            ),
            "size": self.fonts.get(
                f"{prefix}_font_size",
                self.DEFAULT_FONTS.get(f"{prefix}_font_size", "12"),
            ),
            "weight": self.fonts.get(
                f"{prefix}_font_weight",
                self.DEFAULT_FONTS.get(f"{prefix}_font_weight", "Medium"),
            ),
        }

    def set_font(self, prefix: str, family: str, size: str, weight: str):
        """Set font configuration for a prefix.

        Args:
            prefix: Font prefix ("ui" or "node")
            family: Font family name
            size: Font size as string
            weight: Font weight as string
        """
        # Create new dict to trigger property change
        new_fonts = dict(self.fonts)
        new_fonts[f"{prefix}_font_family"] = family
        new_fonts[f"{prefix}_font_size"] = size
        new_fonts[f"{prefix}_font_weight"] = weight
        self.fonts = new_fonts

        # Update state store
        self._update_theme_state()

        # Publish event
        self._event_bus.publish(
            Event(
                type=EventType.THEME_FONT_CHANGED,
                payload={
                    "font_changed": prefix,
                    "family": family,
                    "size": size,
                    "weight": weight,
                },
            )
        )

    def set_theme(
        self, colors: Dict[str, str], fonts: Dict[str, str], theme_name: str = "custom"
    ):
        """Set complete theme.

        Args:
            colors: Dictionary of color values
            fonts: Dictionary of font values
            theme_name: Name of the theme
        """
        self.colors = dict(colors)
        self.fonts = dict(fonts)
        self.current_theme = theme_name

        # Update state store
        self._update_theme_state()

        # Publish event
        self._event_bus.publish(
            Event(type=EventType.THEME_UPDATED, payload={"theme_name": theme_name})
        )

    def reset_to_defaults(self):
        """Reset theme to default values."""
        self.colors = dict(self.DEFAULT_COLORS)
        self.fonts = dict(self.DEFAULT_FONTS)
        self.current_theme = "default"

        # Update state store
        self._update_theme_state()

        # Publish event
        self._event_bus.publish(
            Event(type=EventType.THEME_UPDATED, payload={"reset": True})
        )

    def _update_theme_state(self):
        """Update theme state in state store."""
        new_theme_state = ThemeState(
            colors=dict(self.colors),
            fonts=dict(self.fonts),
            current_theme=self.current_theme,
        )
        self._store.update(theme=new_theme_state)
