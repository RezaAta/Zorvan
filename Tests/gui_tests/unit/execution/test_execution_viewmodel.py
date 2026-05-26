"""
Unit tests for ExecutionViewModel.

Tests the pure Python logic of execution control without any GUI dependencies.
"""

import pytest

from gui_framework.viewmodels.execution_viewmodel import ExecutionViewModel, ExecutionStatus
from gui_framework.events.bus import Event, EventType
from gui_framework.events import bus as event_bus_module
from gui_framework.events.bus import get_event_bus


@pytest.fixture(autouse=True)
def _clean_execution_events():
    event_bus_module._bus = event_bus_module.EventBus()
    yield
    event_bus_module._bus = event_bus_module.EventBus()


class TestExecutionViewModel:
    """Test suite for ExecutionViewModel."""
    
    def test_initialization(self):
        """Test ViewModel initializes with correct defaults."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        assert vm.status == ExecutionStatus.IDLE
        assert vm.current_step == 0
        assert vm.max_steps == 100
        assert vm.speed_ms == 100
        assert vm.is_max_speed is False
        
        vm.cleanup()
    
    def test_play_starts_execution(self):
        """Test play() starts execution."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        result = vm.play()
        
        assert result is True
        assert vm.status == ExecutionStatus.RUNNING
        assert vm.current_step == 0
        
        vm.cleanup()
    
    def test_play_when_already_running(self):
        """Test play() returns False when already running."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.play()
        result = vm.play()
        
        assert result is False
        assert vm.status == ExecutionStatus.RUNNING
        
        vm.cleanup()
    
    def test_pause_stops_running_execution(self):
        """Test pause() pauses running execution."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.play()
        result = vm.pause()
        
        assert result is True
        assert vm.status == ExecutionStatus.PAUSED
        
        vm.cleanup()
    
    def test_pause_when_not_running(self):
        """Test pause() returns False when not running."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        result = vm.pause()
        
        assert result is False
        assert vm.status == ExecutionStatus.IDLE
        
        vm.cleanup()
    
    def test_resume_from_pause(self):
        """Test resume() resumes from paused state."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.play()
        vm.pause()
        result = vm.resume()
        
        assert result is True
        assert vm.status == ExecutionStatus.RUNNING
        
        vm.cleanup()
    
    def test_resume_from_completed(self):
        """Test resume() extends execution when completed."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        # Simulate completion
        vm.status = ExecutionStatus.COMPLETED
        vm.current_step = 100
        vm.max_steps = 100
        
        result = vm.resume()
        
        assert result is True
        assert vm.status == ExecutionStatus.RUNNING
        assert vm.max_steps == 200  # Extended by max_steps
        
        vm.cleanup()
    
    def test_resume_when_running(self):
        """Test resume() returns False when already running."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.play()
        result = vm.resume()
        
        assert result is False
        assert vm.status == ExecutionStatus.RUNNING
        
        vm.cleanup()
    
    def test_step_executes_single_step(self):
        """Test step() executes a single step."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        result = vm.step()
        
        assert result is True
        assert vm.current_step == 1
        
        vm.cleanup()
    
    def test_step_multiple_times(self):
        """Test step() can be called multiple times."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.step()
        vm.step()
        vm.step()
        
        assert vm.current_step == 3
        
        vm.cleanup()
    
    def test_step_when_running(self):
        """Test step() returns False when running."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.play()
        result = vm.step()
        
        assert result is False
        
        vm.cleanup()
    
    def test_reset_clears_state(self):
        """Test reset() resets execution state."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.play()
        vm.current_step = 50
        
        result = vm.reset()
        
        assert result is True
        assert vm.status == ExecutionStatus.IDLE
        assert vm.current_step == 0
        
        vm.cleanup()
    
    def test_stop_stops_execution(self):
        """Test stop() stops running execution."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.play()
        result = vm.stop()
        
        assert result is True
        assert vm.status == ExecutionStatus.IDLE
        
        vm.cleanup()
    
    def test_stop_when_not_running(self):
        """Test stop() returns False when not running."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        result = vm.stop()
        
        assert result is False
        assert vm.status == ExecutionStatus.IDLE
        
        vm.cleanup()
    
    def test_set_speed(self):
        """Test set_speed() updates speed."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.set_speed(50)
        
        assert vm.speed_ms == 50
        assert vm.is_max_speed is False
        
        vm.cleanup()
    
    def test_set_speed_to_zero(self):
        """Test set_speed(0) enables max speed."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.set_speed(0)
        
        assert vm.speed_ms == 0
        assert vm.is_max_speed is True
        
        vm.cleanup()
    
    def test_set_speed_negative(self):
        """Test set_speed() clamps negative values to 0."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.set_speed(-100)
        
        assert vm.speed_ms == 0
        
        vm.cleanup()
    
    def test_toggle_max_speed_on(self):
        """Test toggle_max_speed() enables max speed."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.speed_ms = 100
        vm.toggle_max_speed()
        
        assert vm.speed_ms == 0
        assert vm.is_max_speed is True
        
        vm.cleanup()
    
    def test_toggle_max_speed_off(self):
        """Test toggle_max_speed() disables max speed."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.speed_ms = 0
        vm.is_max_speed = True
        vm.toggle_max_speed()
        
        assert vm.speed_ms == 100  # Default restore
        assert vm.is_max_speed is False
        
        vm.cleanup()
    
    def test_set_max_steps(self):
        """Test set_max_steps() updates max steps."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.set_max_steps(500)
        
        assert vm.max_steps == 500
        
        vm.cleanup()
    
    def test_set_max_steps_minimum(self):
        """Test set_max_steps() enforces minimum of 1."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        vm.set_max_steps(0)
        assert vm.max_steps == 1
        
        vm.set_max_steps(-10)
        assert vm.max_steps == 1
        
        vm.cleanup()
    
    def test_status_properties(self):
        """Test status check properties."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        # Idle
        assert vm.is_running is False
        assert vm.is_paused is False
        assert vm.is_completed is False
        
        # Running
        vm.play()
        assert vm.is_running is True
        assert vm.is_paused is False
        
        # Paused
        vm.pause()
        assert vm.is_running is False
        assert vm.is_paused is True
        
        # Completed
        vm.status = ExecutionStatus.COMPLETED
        assert vm.is_completed is True
        
        vm.cleanup()
    
    def test_action_availability_properties(self):
        """Test action availability check properties."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        # Idle: can play, step, not pause/resume
        assert vm.can_play is True
        assert vm.can_pause is False
        assert vm.can_resume is False
        assert vm.can_step is True
        assert vm.can_reset is False
        
        # Running: can pause, not play/resume/step
        vm.play()
        assert vm.can_play is False
        assert vm.can_pause is True
        assert vm.can_resume is False
        assert vm.can_step is False
        assert vm.can_reset is True
        
        # Paused: can resume/step/reset, not play/pause
        vm.pause()
        assert vm.can_play is False
        assert vm.can_pause is False
        assert vm.can_resume is True
        assert vm.can_step is True
        assert vm.can_reset is True
        
        # Completed: can play/resume/reset
        vm.status = ExecutionStatus.COMPLETED
        assert vm.can_play is True
        assert vm.can_resume is True
        assert vm.can_reset is True
        
        vm.cleanup()
    
    def test_observable_properties(self):
        """Test observable properties notify observers."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        # Track property changes
        status_changes = []
        step_changes = []
        
        def on_status_changed(old, new):
            status_changes.append((old, new))
        
        def on_step_changed(old, new):
            step_changes.append((old, new))
        
        vm.observe_property("status", on_status_changed)
        vm.observe_property("current_step", on_step_changed)
        
        # Trigger changes
        vm.play()
        vm.step()
        
        assert len(status_changes) > 0
        assert len(step_changes) > 0
        
        vm.cleanup()
    
    def test_event_publishing(self):
        """Test ViewModel publishes events correctly."""
        vm = ExecutionViewModel()
        vm.initialize()
        
        # Track published events
        published_events = []
        
        def capture_event(event):
            published_events.append(event.type)
        
        # Subscribe to all execution events
        vm._event_bus.subscribe(EventType.EXECUTION_STARTED, capture_event)
        vm._event_bus.subscribe(EventType.EXECUTION_PAUSED, capture_event)
        vm._event_bus.subscribe(EventType.EXECUTION_STOPPED, capture_event)
        vm._event_bus.subscribe(EventType.GRAPH_RESET, capture_event)
        
        # Trigger actions
        vm.play()
        vm.pause()
        vm.stop()
        vm.reset()
        
        assert EventType.EXECUTION_STARTED in published_events
        assert EventType.EXECUTION_PAUSED in published_events
        assert EventType.EXECUTION_STOPPED in published_events
        assert EventType.GRAPH_RESET in published_events
        
        vm.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
