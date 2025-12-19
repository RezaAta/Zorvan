"""
Execution ViewModel - Pure Python logic for graph execution control.

Manages execution state (play/pause/step/reset), speed settings, and execution lifecycle.
This ViewModel is completely testable without PyQt dependencies.
"""

from enum import Enum

from ..viewmodels.base import BaseViewModel, ObservableProperty
from ..events.bus import Event, EventType


class ExecutionStatus(Enum):
    """Execution status states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class ExecutionViewModel(BaseViewModel):
    """ViewModel for graph execution control.
    
    Pure Python logic with no PyQt dependencies. Manages execution state,
    speed control, and provides methods for play/pause/step/reset operations.
    
    Attributes:
        status: Current execution status (idle/running/paused/completed)
        current_step: Current iteration/step number
        max_steps: Maximum steps for execution
        speed_ms: Execution speed in milliseconds (0 = max speed)
        is_max_speed: Whether max speed mode is enabled
    """
    
    # Observable properties
    status = ObservableProperty("status", default=ExecutionStatus.IDLE)
    current_step = ObservableProperty("current_step", default=0)
    max_steps = ObservableProperty("max_steps", default=100)
    speed_ms = ObservableProperty("speed_ms", default=100)
    is_max_speed = ObservableProperty("is_max_speed", default=False)
    
    def initialize(self):
        """Initialize the execution ViewModel.
        
        Subscribe to relevant events and set initial state.
        """
        # Subscribe to execution events from external sources
        self._event_bus.subscribe(EventType.EXECUTION_STEP_COMPLETE, self._on_step_complete)
    
    def cleanup(self):
        """Clean up resources and unsubscribe from events."""
        self._event_bus.unsubscribe(EventType.EXECUTION_STEP_COMPLETE, self._on_step_complete)
    
    def play(self) -> bool:
        """Start execution.
        
        Returns:
            True if execution started, False if unable to start
        """
        if self.status == ExecutionStatus.RUNNING:
            return False
        
        # Update status
        self.status = ExecutionStatus.RUNNING
        self.current_step = 0
        
        # Publish event
        self._event_bus.publish(Event(
            type=EventType.EXECUTION_STARTED,
            payload={"max_steps": self.max_steps}
        ))
        
        return True
    
    def pause(self) -> bool:
        """Pause execution.
        
        Returns:
            True if paused, False if not running
        """
        if self.status != ExecutionStatus.RUNNING:
            return False
        
        self.status = ExecutionStatus.PAUSED
        
        # Publish event
        self._event_bus.publish(Event(type=EventType.EXECUTION_PAUSED))
        
        return True
    
    def resume(self) -> bool:
        """Resume execution after pause or completion.
        
        Returns:
            True if resumed, False if unable to resume
        """
        if self.status == ExecutionStatus.RUNNING:
            return False
        
        # Check if execution completed - if so, extend by max_steps
        if self.status == ExecutionStatus.COMPLETED:
            additional_steps = self.max_steps
            new_total = self.current_step + additional_steps
            self.max_steps = new_total
            
            # Publish resume with additional steps
            self._event_bus.publish(Event(
                type=EventType.EXECUTION_STARTED,
                payload={
                    "max_steps": additional_steps,
                    "resume": True,
                    "additional": True
                }
            ))
        else:
            # Normal resume from pause
            self._event_bus.publish(Event(
                type=EventType.EXECUTION_STARTED,
                payload={"resume": True}
            ))
        
        self.status = ExecutionStatus.RUNNING
        
        return True
    
    def step(self) -> bool:
        """Execute a single step.
        
        Returns:
            True if step executed, False if unable to step
        """
        if self.status == ExecutionStatus.RUNNING:
            return False  # Can't step while running
        
        # Increment step
        self.current_step += 1
        
        # Publish step event
        self._event_bus.publish(Event(
            type=EventType.EXECUTION_STEP_COMPLETE,
            payload={"step": self.current_step}
        ))
        
        return True
    
    def reset(self) -> bool:
        """Reset execution to initial state.
        
        Returns:
            True if reset, False if unable to reset
        """
        # Stop execution if running
        if self.status == ExecutionStatus.RUNNING:
            self.stop()
        
        self.status = ExecutionStatus.IDLE
        self.current_step = 0
        
        # Publish reset event
        self._event_bus.publish(Event(type=EventType.GRAPH_RESET))
        
        return True
    
    def stop(self) -> bool:
        """Stop execution.
        
        Returns:
            True if stopped, False if not running
        """
        if self.status not in (ExecutionStatus.RUNNING, ExecutionStatus.PAUSED):
            return False
        
        self.status = ExecutionStatus.IDLE
        
        # Publish event
        self._event_bus.publish(Event(type=EventType.EXECUTION_STOPPED))
        
        return True
    
    def set_speed(self, speed_ms: int):
        """Set execution speed.
        
        Args:
            speed_ms: Speed in milliseconds (0 = max speed)
        """
        if speed_ms < 0:
            speed_ms = 0
        
        self.speed_ms = speed_ms
        self.is_max_speed = (speed_ms == 0)
        
        # Publish event
        self._event_bus.publish(Event(
            type=EventType.EXECUTION_SPEED_CHANGED,
            payload={"speed_ms": speed_ms}
        ))
    
    def toggle_max_speed(self):
        """Toggle max speed mode."""
        if self.is_max_speed:
            # Restore previous speed (default 100ms if not set)
            self.set_speed(100)
        else:
            # Set to max speed (0ms)
            self.set_speed(0)
    
    def set_max_steps(self, steps: int):
        """Set maximum steps for execution.
        
        Args:
            steps: Maximum number of steps
        """
        if steps < 1:
            steps = 1
        
        self.max_steps = steps
    
    # Event handlers
    def _on_step_complete(self, event: Event):
        """Handle step complete event from external sources."""
        payload = event.payload or {}
        step = payload.get("step")
        
        if step is not None:
            self.current_step = step
            
            # Check if execution completed
            if self.current_step >= self.max_steps:
                self.status = ExecutionStatus.COMPLETED
                
                # Publish completion event
                self._event_bus.publish(Event(
                    type=EventType.EXECUTION_STOPPED,
                    payload={"completed": True}
                ))
    
    # Status properties
    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.status == ExecutionStatus.RUNNING
    
    @property
    def is_paused(self) -> bool:
        """Check if execution is paused."""
        return self.status == ExecutionStatus.PAUSED
    
    @property
    def is_completed(self) -> bool:
        """Check if execution has completed."""
        return self.status == ExecutionStatus.COMPLETED
    
    @property
    def can_play(self) -> bool:
        """Check if play action is available."""
        return self.status in (ExecutionStatus.IDLE, ExecutionStatus.COMPLETED)
    
    @property
    def can_pause(self) -> bool:
        """Check if pause action is available."""
        return self.status == ExecutionStatus.RUNNING
    
    @property
    def can_resume(self) -> bool:
        """Check if resume action is available."""
        return self.status in (ExecutionStatus.PAUSED, ExecutionStatus.COMPLETED)
    
    @property
    def can_step(self) -> bool:
        """Check if step action is available."""
        return self.status in (ExecutionStatus.IDLE, ExecutionStatus.PAUSED)
    
    @property
    def can_reset(self) -> bool:
        """Check if reset action is available."""
        return self.status != ExecutionStatus.IDLE or self.current_step > 0
