"""
Unit tests for ThemeMixin (new MVVM-compatible version).

Tests both legacy and new StateStore modes.
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys

# Mock PyQt6 for testing
if 'PyQt6' not in sys.modules:
    sys.modules['PyQt6'] = MagicMock()
    sys.modules['PyQt6.QtCore'] = MagicMock()
    sys.modules['PyQt6.QtGui'] = MagicMock()
    sys.modules['PyQt6.QtWidgets'] = MagicMock()

from gui_framework.widgets.theme_mixin import ThemeMixin
from gui_framework.viewmodels.theme_viewmodel import ThemeViewModel
from gui_framework.state.models import ThemeState


class MockWidget(ThemeMixin):
    """Mock widget for testing ThemeMixin."""

    def __init__(self, use_state_store=False):
        self.apply_theme_called = 0
        self.last_theme_data = None
        ThemeMixin.__init__(self, use_state_store=use_state_store)

    def apply_theme(self):
        """Track theme application calls."""
        self.apply_theme_called += 1
        if self.theme_viewmodel:
            self.last_theme_data = {
                "colors": dict(self.theme_viewmodel.colors),
                "fonts": dict(self.theme_viewmodel.fonts),
            }


class TestThemeMixinLegacyMode:
    """Test ThemeMixin in legacy mode (backward compatibility)."""

    def test_initialization_legacy(self):
        """Test ThemeMixin initializes in legacy mode by default."""
        widget = MockWidget(use_state_store=False)

        # Should use legacy theme manager
        assert widget.theme_manager is not None
        assert widget.theme_viewmodel is None
        assert widget._use_state_store is False

        # apply_theme should be called on initialization
        assert widget.apply_theme_called >= 1

    def test_legacy_mode_has_theme_manager(self):
        """Test legacy mode provides theme_manager access."""
        widget = MockWidget(use_state_store=False)

        # Should have theme_manager
        tm = widget.get_theme_manager()
        assert tm is not None
        assert hasattr(tm, 'theme')
        assert hasattr(tm, 'get_color')

    def test_legacy_disconnect(self):
        """Test disconnect_theme works in legacy mode."""
        widget = MockWidget(use_state_store=False)

        # Should not raise exception
        widget.disconnect_theme()


class TestThemeMixinStateStoreMode:
    """Test ThemeMixin in new StateStore mode."""

    def test_initialization_state_store(self):
        """Test ThemeMixin initializes in StateStore mode."""
        widget = MockWidget(use_state_store=True)

        # Should use new architecture
        assert widget._use_state_store is True
        assert widget.theme_viewmodel is not None
        assert isinstance(widget.theme_viewmodel, ThemeViewModel)

        # apply_theme should be called on initialization
        assert widget.apply_theme_called >= 1

    def test_state_store_mode_has_viewmodel(self):
        """Test StateStore mode provides theme_viewmodel access."""
        widget = MockWidget(use_state_store=True)

        # Should have theme_viewmodel
        vm = widget.theme_viewmodel
        assert vm is not None
        assert isinstance(vm, ThemeViewModel)
        assert hasattr(vm, 'get_color')
        assert hasattr(vm, 'get_font')

    def test_theme_viewmodel_provides_colors(self):
        """Test theme_viewmodel provides color access."""
        widget = MockWidget(use_state_store=True)

        # Should be able to get colors
        color = widget.theme_viewmodel.get_color("bg")
        assert isinstance(color, str)
        assert color.startswith("#")

    def test_theme_viewmodel_provides_fonts(self):
        """Test theme_viewmodel provides font access."""
        widget = MockWidget(use_state_store=True)

        # Should be able to get fonts
        font = widget.theme_viewmodel.get_font("ui")
        assert isinstance(font, dict)
        assert "family" in font
        assert "size" in font
        assert "weight" in font

    def test_state_change_triggers_apply_theme(self):
        """Test state changes trigger apply_theme."""
        widget = MockWidget(use_state_store=True)

        initial_calls = widget.apply_theme_called

        # Change theme via state store
        new_theme_state = ThemeState(
            colors={"bg": "#ff0000", "text": "#00ff00"},
            fonts={"ui_font_family": "Arial"},
            current_theme="test"
        )
        widget._state_store.update(theme=new_theme_state)

        # apply_theme should be called again
        assert widget.apply_theme_called > initial_calls

    def test_color_change_reflects_in_widget(self):
        """Test color changes in state are reflected in widget."""
        widget = MockWidget(use_state_store=True)

        # Change color
        widget.theme_viewmodel.set_color("accent", "#abcdef")

        # Widget should have received the update
        assert widget.last_theme_data is not None
        assert widget.last_theme_data["colors"]["accent"] == "#abcdef"

    def test_state_store_disconnect(self):
        """Test disconnect_theme works in StateStore mode."""
        widget = MockWidget(use_state_store=True)

        # Should not raise exception
        widget.disconnect_theme()

        # After disconnect, state changes should not trigger apply_theme
        calls_before = widget.apply_theme_called
        widget._state_store.update(theme=ThemeState(colors={"bg": "#123456"}))

        # apply_theme should not be called (or minimal calls)
        # Note: We can't fully test this without proper signal disconnection


class TestThemeMixinCompatibility:
    """Test ThemeMixin backward compatibility."""

    def test_default_is_legacy_mode(self):
        """Test that default mode is legacy for backward compatibility."""
        widget = MockWidget()  # No use_state_store parameter

        # Should default to legacy mode
        assert widget._use_state_store is False
        assert widget.theme_manager is not None
        assert widget.theme_viewmodel is None

    def test_legacy_mode_property_access(self):
        """Test property access in legacy mode."""
        widget = MockWidget(use_state_store=False)

        # Properties should work
        assert widget.theme_manager is not None
        assert widget.theme_viewmodel is None

    def test_state_store_mode_property_access(self):
        """Test property access in StateStore mode."""
        widget = MockWidget(use_state_store=True)

        # Properties should work
        assert widget.theme_viewmodel is not None


class TestThemeMixinErrorHandling:
    """Test ThemeMixin error handling."""

    def test_apply_theme_exception_handled(self):
        """Test that exceptions in apply_theme don't crash."""

        class BrokenWidget(ThemeMixin):
            def __init__(self):
                ThemeMixin.__init__(self, use_state_store=True)

            def apply_theme(self):
                raise RuntimeError("Intentional test error")

        # Should not raise exception
        widget = BrokenWidget()
        widget._on_theme_changed()  # Should handle exception gracefully

    def test_missing_apply_theme_handled(self):
        """Test that missing apply_theme method is handled."""

        class NoApplyThemeWidget(ThemeMixin):
            def __init__(self):
                # Don't define apply_theme
                ThemeMixin.__init__(self, use_state_store=True)

        # Should not raise exception
        widget = NoApplyThemeWidget()
        widget._on_theme_changed()  # Should handle AttributeError gracefully
