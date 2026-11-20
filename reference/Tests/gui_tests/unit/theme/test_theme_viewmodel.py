"""
Unit tests for ThemeViewModel.

Tests the pure Python logic of theme management without any GUI dependencies.
"""

import pytest

from gui_framework.events.bus import EventType
from gui_framework.state.models import ThemeState
from gui_framework.viewmodels.theme_viewmodel import ThemeViewModel


class TestThemeViewModel:
    """Test suite for ThemeViewModel."""

    def test_initialization(self):
        """Test ViewModel initializes with default theme."""
        vm = ThemeViewModel()
        vm.initialize()

        assert vm.current_theme == "default"
        assert isinstance(vm.colors, dict)
        assert isinstance(vm.fonts, dict)
        assert len(vm.colors) > 0
        assert len(vm.fonts) > 0

        vm.cleanup()

    def test_default_colors(self):
        """Test default color values are set correctly."""
        vm = ThemeViewModel()
        # Reset to defaults before initializing
        vm._store.update(theme=ThemeState())
        vm.initialize()

        # Check some key colors
        assert vm.get_color("bg") == "#2b2b2b"
        assert vm.get_color("text") == "#bbbbbb"
        assert vm.get_color("accent") == "#4a86e8"
        assert vm.get_color("canvas_bg") == "#232526"

        vm.cleanup()

    def test_default_fonts(self):
        """Test default font values are set correctly."""
        vm = ThemeViewModel()
        vm.initialize()

        # Check UI font
        ui_font = vm.get_font("ui")
        assert ui_font["family"] == "Oswald"
        assert ui_font["size"] == "12"
        assert ui_font["weight"] == "Medium"

        # Check node font
        node_font = vm.get_font("node")
        assert node_font["family"] == "Oswald"
        assert node_font["size"] == "10"
        assert node_font["weight"] == "Medium"

        vm.cleanup()

    def test_get_color_with_fallback(self):
        """Test get_color returns fallback for missing keys."""
        vm = ThemeViewModel()
        # Reset to defaults before initializing
        vm._store.update(theme=ThemeState())
        vm.initialize()

        # Existing color
        assert vm.get_color("bg") == "#2b2b2b"

        # Non-existing color with fallback
        assert vm.get_color("nonexistent", "#ff0000") == "#ff0000"

        vm.cleanup()

    def test_set_color(self):
        """Test setting a color value."""
        vm = ThemeViewModel()
        vm.initialize()

        # Set a color
        vm.set_color("bg", "#123456")

        # Verify it was set
        assert vm.get_color("bg") == "#123456"

        # Other colors should remain unchanged
        assert vm.get_color("text") == "#bbbbbb"

        vm.cleanup()

    def test_set_color_publishes_event(self):
        """Test that setting a color publishes a THEME_FONT_CHANGED event."""
        vm = ThemeViewModel()
        vm.initialize()

        # Subscribe to events
        events = []

        def handler(event):
            events.append(event)

        vm._event_bus.subscribe(EventType.THEME_COLOR_CHANGED, handler)

        # Set a color
        vm.set_color("accent", "#ff00ff")

        # Verify event was published
        assert len(events) == 1
        assert events[0].type == EventType.THEME_COLOR_CHANGED
        assert events[0].payload["color_changed"] == "accent"
        assert events[0].payload["value"] == "#ff00ff"

        vm.cleanup()

    def test_set_font(self):
        """Test setting font configuration."""
        vm = ThemeViewModel()
        vm.initialize()

        # Set UI font
        vm.set_font("ui", "Arial", "14", "Bold")

        # Verify it was set
        ui_font = vm.get_font("ui")
        assert ui_font["family"] == "Arial"
        assert ui_font["size"] == "14"
        assert ui_font["weight"] == "Bold"

        # Node font should remain unchanged
        node_font = vm.get_font("node")
        assert node_font["family"] == "Oswald"

        vm.cleanup()

    def test_set_font_publishes_event(self):
        """Test that setting a font publishes a THEME_FONT_CHANGED event."""
        vm = ThemeViewModel()
        vm.initialize()

        # Subscribe to events
        events = []

        def handler(event):
            events.append(event)

        vm._event_bus.subscribe(EventType.THEME_FONT_CHANGED, handler)

        # Set a font
        vm.set_font("node", "Verdana", "11", "Normal")

        # Verify event was published
        assert len(events) == 1
        assert events[0].type == EventType.THEME_FONT_CHANGED
        assert events[0].payload["font_changed"] == "node"
        assert events[0].payload["family"] == "Verdana"

        vm.cleanup()

    def test_set_theme(self):
        """Test setting complete theme."""
        vm = ThemeViewModel()
        vm.initialize()

        # Create custom theme
        colors = {
            "bg": "#000000",
            "text": "#ffffff",
            "accent": "#00ff00",
        }
        fonts = {
            "ui_font_family": "Courier",
            "ui_font_size": "16",
        }

        vm.set_theme(colors, fonts, "custom")

        # Verify theme was set
        assert vm.current_theme == "custom"
        assert vm.get_color("bg") == "#000000"
        assert vm.get_color("text") == "#ffffff"
        assert vm.get_font("ui")["family"] == "Courier"

        vm.cleanup()

    def test_set_theme_publishes_event(self):
        """Test that setting theme publishes a THEME_FONT_CHANGED event."""
        vm = ThemeViewModel()
        vm.initialize()

        # Subscribe to events
        events = []

        def handler(event):
            events.append(event)

        vm._event_bus.subscribe(EventType.THEME_UPDATED, handler)

        # Set theme
        vm.set_theme({}, {}, "dark")

        # Verify event was published
        assert len(events) == 1
        assert events[0].type == EventType.THEME_UPDATED
        assert events[0].payload["theme_name"] == "dark"

        vm.cleanup()

    def test_reset_to_defaults(self):
        """Test resetting theme to defaults."""
        vm = ThemeViewModel()
        vm.initialize()

        # Modify theme
        vm.set_color("bg", "#ffffff")
        vm.set_font("ui", "Arial", "20", "Bold")

        # Reset to defaults
        vm.reset_to_defaults()

        # Verify defaults were restored
        assert vm.current_theme == "default"
        assert vm.get_color("bg") == "#2b2b2b"
        ui_font = vm.get_font("ui")
        assert ui_font["family"] == "Oswald"
        assert ui_font["size"] == "12"

        vm.cleanup()

    def test_reset_publishes_event(self):
        """Test that reset publishes a THEME_FONT_CHANGED event."""
        vm = ThemeViewModel()
        vm.initialize()

        # Subscribe to events
        events = []

        def handler(event):
            events.append(event)

        vm._event_bus.subscribe(EventType.THEME_UPDATED, handler)

        # Reset
        vm.reset_to_defaults()

        # Verify event was published
        assert len(events) == 1
        assert events[0].type == EventType.THEME_UPDATED
        assert events[0].payload["reset"] is True

        vm.cleanup()

    def test_observable_colors_property(self):
        """Test that colors property is observable."""
        vm = ThemeViewModel()
        vm.initialize()

        # Observe colors property
        callback_called = []

        def callback(old_value, new_value):
            callback_called.append((old_value, new_value))

        vm.observe_property("colors", callback)

        # Change color
        vm.set_color("bg", "#abcdef")

        # Verify callback was called
        assert len(callback_called) == 1
        assert callback_called[0][1]["bg"] == "#abcdef"

        vm.cleanup()

    def test_observable_fonts_property(self):
        """Test that fonts property is observable."""
        vm = ThemeViewModel()
        vm.initialize()

        # Observe fonts property
        callback_called = []

        def callback(old_value, new_value):
            callback_called.append((old_value, new_value))

        vm.observe_property("fonts", callback)

        # Change font
        vm.set_font("ui", "Times", "18", "Light")

        # Verify callback was called
        assert len(callback_called) == 1
        assert callback_called[0][1]["ui_font_family"] == "Times"

        vm.cleanup()

    def test_observable_current_theme_property(self):
        """Test that current_theme property is observable."""
        vm = ThemeViewModel()
        vm.initialize()

        # Observe current_theme property
        callback_called = []

        def callback(old_value, new_value):
            callback_called.append((old_value, new_value))

        vm.observe_property("current_theme", callback)

        # Change theme
        vm.set_theme({}, {}, "dark")

        # Verify callback was called
        assert len(callback_called) == 1
        assert callback_called[0][0] == "default"
        assert callback_called[0][1] == "dark"

        vm.cleanup()

    def test_store_integration(self):
        """Test that theme state is updated in state store."""
        vm = ThemeViewModel()
        vm.initialize()

        # Set a color
        vm.set_color("accent", "#ff0000")

        # Verify state store was updated
        state = vm._store.get_state()
        assert state.theme.colors["accent"] == "#ff0000"

        vm.cleanup()

    def test_load_theme_from_store(self):
        """Test loading theme from state store on initialization."""
        vm = ThemeViewModel()

        # Set up state store with custom theme
        theme_state = ThemeState(
            colors={"bg": "#123456", "text": "#fedcba"},
            fonts={"ui_font_family": "Comic Sans"},
            current_theme="loaded",
        )
        vm._store.update(theme=theme_state)

        # Initialize (should load from state)
        vm.initialize()

        # Verify theme was loaded
        assert vm.current_theme == "loaded"
        assert vm.get_color("bg") == "#123456"
        assert vm.get_font("ui")["family"] == "Comic Sans"

        vm.cleanup()

    def test_multiple_color_changes(self):
        """Test multiple color changes in sequence."""
        vm = ThemeViewModel()
        vm.initialize()

        # Change multiple colors
        vm.set_color("bg", "#111111")
        vm.set_color("text", "#999999")
        vm.set_color("accent", "#ff00ff")

        # Verify all changes
        assert vm.get_color("bg") == "#111111"
        assert vm.get_color("text") == "#999999"
        assert vm.get_color("accent") == "#ff00ff"

        vm.cleanup()

    def test_theme_immutability(self):
        """Test that setting colors creates new dict (immutability)."""
        vm = ThemeViewModel()
        vm.initialize()

        # Get reference to original colors
        original_colors = vm.colors
        original_id = id(original_colors)

        # Set a color
        vm.set_color("bg", "#abcdef")

        # Verify new dict was created
        assert id(vm.colors) != original_id
        assert vm.colors is not original_colors

        vm.cleanup()
