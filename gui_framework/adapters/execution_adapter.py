"""
Execution Adapter - Bridges MVVM ExecutionViewModel with legacy GraphRunner.

This adapter enables incremental migration from the legacy execution controller
to the MVVM pattern by translating between the two systems.
"""

import logging
from typing import TYPE_CHECKING, Optional

from ..events.bus import Event, EventType, get_event_bus
from ..viewmodels.execution_viewmodel import ExecutionStatus, ExecutionViewModel

if TYPE_CHECKING:
    from .legacy import GraphRunner
    from gui_framework.main_window import MainWindow

logger = logging.getLogger(__name__)


class ExecutionAdapter:
    """
    Adapter that bridges MVVM ExecutionViewModel with legacy GraphRunner.

    This allows the new MVVM ExecutionView to control execution while
    the legacy GraphRunner handles actual graph processing.

    Usage:
        adapter = ExecutionAdapter(main_window)
        adapter.connect()  # Wire up signals

        # Now the MVVM ExecutionView controls the legacy execution
    """

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize the execution adapter.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window
        self.event_bus = get_event_bus()
        self._subscriptions = []

        # Create the MVVM ViewModel
        initial_max_steps = 100
        initial_speed_ms = 100

        try:
            if hasattr(main_window, "max_steps_spin") and main_window.max_steps_spin:
                initial_max_steps = main_window.max_steps_spin.value()
        except Exception:
            pass

        try:
            if hasattr(main_window, "speed_slider") and main_window.speed_slider:
                initial_speed_ms = main_window.speed_slider.value()
        except Exception:
            pass

        self.viewmodel = ExecutionViewModel(
            max_steps=initial_max_steps, speed_ms=initial_speed_ms
        )
        self.viewmodel.initialize()

    @property
    def graph_runner(self) -> Optional["GraphRunner"]:
        """Access the graph runner from main window."""
        return getattr(self.main_window, "graph_runner", None)

    @property
    def execution_controller(self):
        """Access the legacy execution controller."""
        return getattr(self.main_window, "execution_controller", None)

    def connect(self):
        """Wire up event subscriptions between MVVM and legacy systems."""
        # Subscribe to MVVM events and forward to legacy
        self._subscriptions.append(
            self.event_bus.subscribe(EventType.EXECUTION_STARTED, self._on_vm_play)
        )
        self._subscriptions.append(
            self.event_bus.subscribe(EventType.EXECUTION_PAUSED, self._on_vm_pause)
        )
        self._subscriptions.append(
            self.event_bus.subscribe(EventType.EXECUTION_STOPPED, self._on_vm_stop)
        )
        self._subscriptions.append(
            self.event_bus.subscribe(EventType.GRAPH_RESET, self._on_vm_reset)
        )
        self._subscriptions.append(
            self.event_bus.subscribe(
                EventType.EXECUTION_SPEED_CHANGED, self._on_vm_speed_changed
            )
        )

        # Connect legacy GraphRunner signals to update MVVM state
        if self.graph_runner:
            try:
                self.graph_runner.step_completed.connect(self._on_legacy_step_completed)
                self.graph_runner.execution_finished.connect(
                    self._on_legacy_execution_finished
                )
            except Exception as e:
                logger.warning("Failed to connect GraphRunner signals: %s", e)

        # Connect to legacy max_steps_spin changes to sync with MVVM
        try:
            if (
                hasattr(self.main_window, "max_steps_spin")
                and self.main_window.max_steps_spin
            ):
                self.main_window.max_steps_spin.valueChanged.connect(
                    self._on_legacy_max_steps_changed
                )
        except Exception:
            pass

        logger.debug("ExecutionAdapter connected")

    def disconnect(self):
        """Unsubscribe from events."""
        for unsub_fn in self._subscriptions:
            try:
                if callable(unsub_fn):
                    unsub_fn()
            except Exception:
                pass
        self._subscriptions.clear()

        # Cleanup viewmodel
        try:
            self.viewmodel.cleanup()
        except Exception:
            pass

        logger.debug("ExecutionAdapter disconnected")

    # MVVM -> Legacy event handlers

    def _on_vm_play(self, event: Event):
        """Handle play event from MVVM ViewModel."""
        payload = event.payload or {}

        # Check if this is a resume after completion
        if payload.get("resume") and payload.get("additional"):
            # Resume with additional steps
            self._do_legacy_resume()
        elif payload.get("resume"):
            # Normal resume from pause
            self._do_legacy_resume()
        else:
            # Fresh start
            self._do_legacy_play()

    def _on_vm_pause(self, event: Event):
        """Handle pause event from MVVM ViewModel."""
        self._do_legacy_pause()

    def _on_vm_stop(self, event: Event):
        """Handle stop event from MVVM ViewModel."""
        # Stop is essentially a pause in legacy system
        self._do_legacy_pause()

    def _on_vm_reset(self, event: Event):
        """Handle reset event from MVVM ViewModel."""
        self._do_legacy_reset()

    def _on_vm_speed_changed(self, event: Event):
        """Handle speed change from MVVM ViewModel."""
        payload = event.payload or {}
        speed_ms = payload.get("speed_ms", 100)
        self._sync_speed_to_legacy(speed_ms)

    # Legacy -> MVVM signal handlers

    def _on_legacy_step_completed(self, step: int):
        """Handle step completion from legacy GraphRunner."""
        # Update MVVM viewmodel state
        self.viewmodel.current_step = step

        # Publish event for other MVVM components
        self.event_bus.publish(
            Event(type=EventType.EXECUTION_STEP_COMPLETE, payload={"step": step})
        )

    def _on_legacy_max_steps_changed(self, value: int):
        """Handle max steps change from legacy spinbox."""
        # Update MVVM viewmodel to keep in sync
        self.viewmodel.max_steps = value

    def _on_legacy_execution_finished(self):
        """Handle execution finish from legacy GraphRunner."""
        self.viewmodel.status = ExecutionStatus.COMPLETED

    # Legacy execution methods

    def _do_legacy_play(self):
        """Start execution via legacy system."""
        try:
            # Sync max_steps from viewmodel to legacy
            if hasattr(self.main_window, "max_steps_spin"):
                self.main_window.max_steps_spin.setValue(self.viewmodel.max_steps)

            # Use legacy controller or direct method
            if self.execution_controller:
                self.execution_controller.play()
            elif hasattr(self.main_window, "play_graph"):
                self.main_window.play_graph()
        except Exception as e:
            logger.error("Failed to start legacy execution: %s", e)

    def _do_legacy_pause(self):
        """Pause execution via legacy system."""
        try:
            if self.execution_controller:
                self.execution_controller.pause()
            elif hasattr(self.main_window, "pause_graph"):
                self.main_window.pause_graph()
        except Exception as e:
            logger.error("Failed to pause legacy execution: %s", e)

    def _do_legacy_resume(self):
        """Resume execution via legacy system."""
        try:
            if self.execution_controller:
                self.execution_controller.resume()
            elif hasattr(self.main_window, "resume_graph"):
                self.main_window.resume_graph()
        except Exception as e:
            logger.error("Failed to resume legacy execution: %s", e)

    def _do_legacy_reset(self):
        """Reset via legacy system."""
        try:
            if self.execution_controller:
                self.execution_controller.reset()
            elif hasattr(self.main_window, "reset_graph"):
                self.main_window.reset_graph()
        except Exception as e:
            logger.error("Failed to reset legacy execution: %s", e)

    def _sync_speed_to_legacy(self, speed_ms: int):
        """Sync speed setting to legacy system."""
        try:
            if hasattr(self.main_window, "speed_slider"):
                self.main_window.speed_slider.setValue(speed_ms)

            if self.graph_runner:
                self.graph_runner.set_speed(speed_ms)
        except Exception as e:
            logger.debug("Could not sync speed to legacy: %s", e)

    # Public API for external use

    def sync_from_legacy(self):
        """Sync current state from legacy system to MVVM."""
        try:
            # Sync max_steps
            if hasattr(self.main_window, "max_steps_spin"):
                self.viewmodel.max_steps = self.main_window.max_steps_spin.value()

            # Sync speed
            if hasattr(self.main_window, "speed_slider"):
                self.viewmodel.speed_ms = self.main_window.speed_slider.value()

            # Sync current step
            if self.graph_runner:
                self.viewmodel.current_step = getattr(
                    self.graph_runner, "current_step", 0
                )

        except Exception as e:
            logger.debug("Could not sync from legacy: %s", e)

    def sync_to_legacy(self):
        """Sync current state from MVVM to legacy system."""
        try:
            if hasattr(self.main_window, "max_steps_spin"):
                self.main_window.max_steps_spin.setValue(self.viewmodel.max_steps)

            if hasattr(self.main_window, "speed_slider"):
                self.main_window.speed_slider.setValue(self.viewmodel.speed_ms)
        except Exception as e:
            logger.debug("Could not sync to legacy: %s", e)
