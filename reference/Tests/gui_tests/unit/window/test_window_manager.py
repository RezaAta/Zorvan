"""
Unit tests for window manager.

Tests WindowManager coordination (without actual PyQt windows).
"""

from unittest.mock import Mock

import pytest

from gui_framework.window.manager import WindowManager, get_window_manager


class MockWindow:
    """Mock window for testing without PyQt."""

    def __init__(self):
        self.shown = False
        self.hidden = False
        self.closed = False

    def show(self):
        self.shown = True

    def hide(self):
        self.hidden = True

    def close(self):
        self.closed = True


class TestWindowManager:
    """Tests for WindowManager class."""

    def test_initialization(self):
        """Test manager initializes empty."""
        manager = WindowManager()

        assert manager.get_window_count() == 0
        assert manager.get_active_window() is None

    def test_register_window(self):
        """Test registering a window."""
        manager = WindowManager()
        window = MockWindow()

        manager.register_main_window("main", window)

        assert manager.get_window_count() == 1
        assert manager.get_window("main") is window

    def test_register_duplicate_raises(self):
        """Test that registering duplicate name raises error."""
        manager = WindowManager()
        window = MockWindow()

        manager.register_main_window("main", window)

        with pytest.raises(ValueError, match="already registered"):
            manager.register_main_window("main", MockWindow())

    def test_first_window_becomes_active(self):
        """Test that first registered window becomes active."""
        manager = WindowManager()
        window = MockWindow()

        manager.register_main_window("main", window)

        assert manager.get_active_window_name() == "main"

    def test_show_window(self):
        """Test showing a window."""
        manager = WindowManager()
        window = MockWindow()

        manager.register_main_window("main", window)
        manager.show_window("main")

        assert window.shown
        assert manager.get_active_window_name() == "main"

    def test_show_unregistered_raises(self):
        """Test that showing unregistered window raises error."""
        manager = WindowManager()

        with pytest.raises(ValueError, match="not registered"):
            manager.show_window("nonexistent")

    def test_hide_window(self):
        """Test hiding a window."""
        manager = WindowManager()
        window = MockWindow()

        manager.register_main_window("main", window)
        manager.hide_window("main")

        assert window.hidden

    def test_close_window(self):
        """Test closing a window."""
        manager = WindowManager()
        window = MockWindow()

        manager.register_main_window("main", window)
        manager.close_window("main")

        assert window.closed
        assert manager.get_window_count() == 0

    def test_unregister_window(self):
        """Test unregistering a window."""
        manager = WindowManager()
        window = MockWindow()

        manager.register_main_window("main", window)
        assert manager.get_window_count() == 1

        manager.unregister_window("main")
        assert manager.get_window_count() == 0

    def test_get_all_windows(self):
        """Test getting all windows."""
        manager = WindowManager()
        window1 = MockWindow()
        window2 = MockWindow()

        manager.register_main_window("win1", window1)
        manager.register_main_window("win2", window2)

        all_windows = manager.get_all_windows()
        assert len(all_windows) == 2
        assert "win1" in all_windows
        assert "win2" in all_windows

    def test_shutdown(self):
        """Test shutting down manager."""
        manager = WindowManager()
        window1 = MockWindow()
        window2 = MockWindow()

        manager.register_main_window("win1", window1)
        manager.register_main_window("win2", window2)

        manager.shutdown()

        assert window1.closed
        assert window2.closed
        assert manager.get_window_count() == 0

    def test_active_window_updates(self):
        """Test that active window updates when showing different window."""
        manager = WindowManager()
        window1 = MockWindow()
        window2 = MockWindow()

        manager.register_main_window("win1", window1)
        manager.register_main_window("win2", window2)

        assert manager.get_active_window_name() == "win1"  # First becomes active

        manager.show_window("win2")

        assert manager.get_active_window_name() == "win2"

    def test_unregister_active_window(self):
        """Test unregistering the active window."""
        manager = WindowManager()
        window1 = MockWindow()
        window2 = MockWindow()

        manager.register_main_window("win1", window1)
        manager.register_main_window("win2", window2)

        assert manager.get_active_window_name() == "win1"

        manager.unregister_window("win1")

        # Should switch to another window
        assert manager.get_active_window_name() == "win2"
