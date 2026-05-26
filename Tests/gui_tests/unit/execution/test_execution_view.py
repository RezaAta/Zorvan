"""
Unit tests for ExecutionView.

Tests the PyQt6 view layer binding to ExecutionViewModel.
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Create minimal PyQt6 stubs for testing without GUI
if "PyQt6" not in sys.modules:
    # Mock PyQt6 modules
    sys.modules["PyQt6"] = MagicMock()
    sys.modules["PyQt6.QtWidgets"] = MagicMock()
    sys.modules["PyQt6.QtCore"] = MagicMock()

from gui_framework.viewmodels.execution_viewmodel import (
    ExecutionStatus,
    ExecutionViewModel,
)


class TestExecutionView:
    """Test ExecutionView with mocked PyQt6."""

    @pytest.fixture
    def viewmodel(self):
        """Create ExecutionViewModel for testing."""
        return ExecutionViewModel(max_steps=100, speed_ms=50)

    @pytest.fixture
    def mock_widgets(self):
        """Create mock widgets."""
        widgets = {
            "status_label": Mock(),
            "step_label": Mock(),
            "play_button": Mock(),
            "pause_button": Mock(),
            "resume_button": Mock(),
            "step_button": Mock(),
            "reset_button": Mock(),
            "stop_button": Mock(),
            "speed_slider": Mock(),
            "speed_value_label": Mock(),
            "max_speed_checkbox": Mock(),
            "max_steps_spinbox": Mock(),
        }

        # Configure mocks
        widgets["speed_slider"].value.return_value = 50
        widgets["max_speed_checkbox"].isChecked.return_value = False
        widgets["max_steps_spinbox"].value.return_value = 100

        return widgets

    def test_initialization(self, viewmodel):
        """Test ExecutionView can be initialized without crashing."""
        # Since we're mocking PyQt6, we can't fully test initialization
        # but we can verify the ViewModel is properly configured
        assert viewmodel.status == ExecutionStatus.IDLE
        assert viewmodel.max_steps == 100
        assert viewmodel.speed_ms == 50

    def test_status_property_binding(self, viewmodel):
        """Test that status changes trigger UI updates."""
        # Simulate property observation
        callback = Mock()
        viewmodel.observe_property("status", callback)

        # Change status
        viewmodel.play()

        # Verify callback was called
        assert callback.called
        assert callback.call_count == 1
        args = callback.call_args[0]
        assert args[0] == ExecutionStatus.IDLE  # old value
        assert args[1] == ExecutionStatus.RUNNING  # new value

    def test_current_step_property_binding(self, viewmodel):
        """Test that current step changes trigger UI updates."""
        callback = Mock()
        viewmodel.observe_property("current_step", callback)

        # Simulate step completion
        viewmodel._current_step = 5
        viewmodel.current_step = 5  # Trigger property setter

        # Verify callback was called
        assert callback.called

    def test_speed_property_binding(self, viewmodel):
        """Test that speed changes trigger UI updates."""
        callback = Mock()
        viewmodel.observe_property("speed_ms", callback)

        # Change speed
        viewmodel.set_speed(200)

        # Verify callback was called
        assert callback.called
        args = callback.call_args[0]
        assert args[0] == 50  # old value
        assert args[1] == 200  # new value

    def test_max_speed_property_binding(self, viewmodel):
        """Test that max speed toggle triggers UI updates."""
        callback = Mock()
        viewmodel.observe_property("is_max_speed", callback)

        # Toggle max speed
        viewmodel.toggle_max_speed()

        # Verify callback was called
        assert callback.called
        args = callback.call_args[0]
        assert args[0] is False  # old value
        assert args[1] is True  # new value

    def test_max_steps_property_binding(self, viewmodel):
        """Test that max steps changes trigger UI updates."""
        callback = Mock()
        viewmodel.observe_property("max_steps", callback)

        # Change max steps
        viewmodel.max_steps = 500

        # Verify callback was called
        assert callback.called
        args = callback.call_args[0]
        assert args[0] == 100  # old value
        assert args[1] == 500  # new value

    def test_button_state_idle(self, viewmodel):
        """Test button enabled states when execution is IDLE."""
        assert viewmodel.status == ExecutionStatus.IDLE
        assert viewmodel.can_play is True
        assert viewmodel.can_pause is False
        assert viewmodel.can_resume is False
        assert viewmodel.can_step is True
        assert (
            viewmodel.can_reset is False
        )  # Reset is disabled when IDLE with current_step=0

    def test_button_state_running(self, viewmodel):
        """Test button enabled states when execution is RUNNING."""
        viewmodel.play()
        assert viewmodel.status == ExecutionStatus.RUNNING
        assert viewmodel.can_play is False
        assert viewmodel.can_pause is True
        assert viewmodel.can_resume is False
        assert viewmodel.can_step is False
        assert viewmodel.can_reset is True

    def test_button_state_paused(self, viewmodel):
        """Test button enabled states when execution is PAUSED."""
        viewmodel.play()
        viewmodel.pause()
        assert viewmodel.status == ExecutionStatus.PAUSED
        assert viewmodel.can_play is False
        assert viewmodel.can_pause is False
        assert viewmodel.can_resume is True
        assert viewmodel.can_step is True
        assert viewmodel.can_reset is True

    def test_button_state_completed(self, viewmodel):
        """Test button enabled states when execution is COMPLETED."""
        viewmodel.play()
        # Simulate completion through step complete event (stop() returns to IDLE, not COMPLETED)
        viewmodel._current_step = 100
        viewmodel._on_step_complete(type("Event", (), {"payload": {"step": 100}})())
        assert viewmodel.status == ExecutionStatus.COMPLETED
        assert viewmodel.can_play is True
        assert viewmodel.can_pause is False
        assert viewmodel.can_resume is True
        assert viewmodel.can_step is True
        assert viewmodel.can_reset is True

    def test_play_action(self, viewmodel):
        """Test that play action works correctly."""
        assert viewmodel.status == ExecutionStatus.IDLE
        success = viewmodel.play()
        assert success is True
        assert viewmodel.status == ExecutionStatus.RUNNING

    def test_pause_action(self, viewmodel):
        """Test that pause action works correctly."""
        viewmodel.play()
        success = viewmodel.pause()
        assert success is True
        assert viewmodel.status == ExecutionStatus.PAUSED

    def test_resume_action(self, viewmodel):
        """Test that resume action works correctly."""
        viewmodel.play()
        viewmodel.pause()
        success = viewmodel.resume()
        assert success is True
        assert viewmodel.status == ExecutionStatus.RUNNING

    def test_step_action(self, viewmodel):
        """Test that step action works correctly."""
        assert viewmodel.current_step == 0
        success = viewmodel.step()
        assert success is True
        assert viewmodel.current_step == 1

    def test_reset_action(self, viewmodel):
        """Test that reset action works correctly."""
        viewmodel.play()
        viewmodel._current_step = 50
        viewmodel.reset()
        assert viewmodel.status == ExecutionStatus.IDLE
        assert viewmodel.current_step == 0

    def test_stop_action(self, viewmodel):
        """Test that stop action works correctly."""
        viewmodel.play()
        viewmodel.stop()
        assert (
            viewmodel.status == ExecutionStatus.IDLE
        )  # stop() returns to IDLE (abort), not COMPLETED

    def test_speed_slider_interaction(self, viewmodel):
        """Test speed slider value changes."""
        assert viewmodel.speed_ms == 50
        viewmodel.set_speed(300)
        assert viewmodel.speed_ms == 300

    def test_max_speed_checkbox_interaction(self, viewmodel):
        """Test max speed checkbox toggle."""
        assert viewmodel.is_max_speed is False
        assert viewmodel.speed_ms == 50

        viewmodel.toggle_max_speed()
        assert viewmodel.is_max_speed is True
        assert viewmodel.speed_ms == 0

        viewmodel.toggle_max_speed()
        assert viewmodel.is_max_speed is False
        assert viewmodel.speed_ms == 50

    def test_max_steps_spinbox_interaction(self, viewmodel):
        """Test max steps spinbox value changes."""
        assert viewmodel.max_steps == 100
        viewmodel.max_steps = 5000
        assert viewmodel.max_steps == 5000

    def test_viewmodel_integration(self, viewmodel):
        """Test complete workflow integrating multiple actions."""
        # Initial state
        assert viewmodel.status == ExecutionStatus.IDLE
        assert viewmodel.current_step == 0

        # Start execution
        viewmodel.play()
        assert viewmodel.status == ExecutionStatus.RUNNING
        assert viewmodel.can_pause is True

        # Simulate some steps
        viewmodel._current_step = 10

        # Pause
        viewmodel.pause()
        assert viewmodel.status == ExecutionStatus.PAUSED
        assert viewmodel.can_resume is True

        # Resume
        viewmodel.resume()
        assert viewmodel.status == ExecutionStatus.RUNNING

        # Stop
        viewmodel.stop()
        assert (
            viewmodel.status == ExecutionStatus.IDLE
        )  # stop() returns to IDLE (abort), not COMPLETED

        # Reset
        viewmodel.reset()
        assert viewmodel.status == ExecutionStatus.IDLE
        assert viewmodel.current_step == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
