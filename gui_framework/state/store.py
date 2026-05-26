"""
Central state store with immutable state and time-travel debugging.

The StateStore provides:
- Immutable state management
- Observable state changes via subscriptions
- Time-travel debugging (undo/redo through state history)
- Thread-safe state updates
"""

from enum import Enum
from threading import RLock
from typing import Any, Callable, Dict, List

from .models import AppState


class StateEvent(Enum):
    """Events triggered by state changes."""

    # General state events
    STATE_CHANGED = "state_changed"

    # Graph events
    GRAPH_CHANGED = "graph_changed"

    # Execution events
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PAUSED = "execution_paused"
    EXECUTION_STOPPED = "execution_stopped"
    EXECUTION_STEP = "execution_step"

    # Canvas events
    SELECTION_CHANGED = "selection_changed"
    ZOOM_CHANGED = "zoom_changed"
    PAN_CHANGED = "pan_changed"

    # Theme events
    THEME_CHANGED = "theme_changed"

    # File events
    FILE_OPENED = "file_opened"
    FILE_SAVED = "file_saved"


class StateStore:
    """
    Central state store with immutable state and time-travel debugging.

    All state updates are immutable - they create new state objects rather
    than modifying existing ones. This enables time-travel debugging and
    makes state changes explicit and traceable.

    Thread-safe for GUI updates using a reentrant lock.

    Example:
        >>> store = get_store()
        >>> state = store.get_state()
        >>> print(state.execution.is_running)
        False
        >>> store.update(execution=ExecutionState(is_running=True))
        >>> print(store.get_state().execution.is_running)
        True
    """

    def __init__(self):
        """Initialize state store with empty state."""
        self._state: AppState = AppState()
        self._history: List[AppState] = [self._state]
        self._history_index: int = 0
        self._max_history: int = 100  # Limit history size
        self._subscribers: Dict[StateEvent, List[Callable]] = {}
        self._lock = RLock()  # Reentrant lock for thread safety

    def get_state(self) -> AppState:
        """
        Get current immutable state snapshot.

        Returns:
            Current application state (immutable)
        """
        with self._lock:
            return self._state

    def update(self, **changes) -> None:
        """
        Update state immutably.

        Creates a new state object with the specified changes. The old state
        remains unchanged (immutability).

        Args:
            **changes: Keyword arguments for state slices to update.
                      Keys should match AppState attributes.

        Example:
            >>> store.update(execution=ExecutionState(is_running=True))
            >>> store.update(
            ...     canvas=CanvasState(zoom_level=1.5),
            ...     file_path="/path/to/file.drawio"
            ... )
        """
        with self._lock:
            # Create new state with changes (immutable update)
            state_dict = {**self._state.__dict__, **changes}
            new_state = AppState(**state_dict)

            self._state = new_state

            # Add to history (for time-travel debugging)
            # Trim future history if we're not at the end
            self._history = self._history[: self._history_index + 1]
            self._history.append(new_state)
            self._history_index += 1

            # Limit history size
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]
                self._history_index = len(self._history) - 1

            # Notify subscribers
            self._notify_subscribers(changes.keys())

    def subscribe(self, event: StateEvent, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to state change events.

        Args:
            event: The state event to subscribe to
            callback: Function to call when event occurs.
                     Receives the changed state slice as argument.

        Example:
            >>> def on_execution_changed(execution_state):
            ...     print(f"Execution running: {execution_state.is_running}")
            >>> store.subscribe(StateEvent.EXECUTION_STARTED, on_execution_changed)
        """
        with self._lock:
            if event not in self._subscribers:
                self._subscribers[event] = []
            if callback not in self._subscribers[event]:
                self._subscribers[event].append(callback)

    def unsubscribe(self, event: StateEvent, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe from state change events.

        Args:
            event: The state event to unsubscribe from
            callback: The callback function to remove
        """
        with self._lock:
            if event in self._subscribers and callback in self._subscribers[event]:
                self._subscribers[event].remove(callback)

    def undo(self) -> bool:
        """
        Time-travel: go back one state in history.

        Returns:
            True if undo was successful, False if at beginning of history
        """
        with self._lock:
            if self._history_index > 0:
                self._history_index -= 1
                self._state = self._history[self._history_index]
                self._notify_all_subscribers()
                return True
            return False

    def redo(self) -> bool:
        """
        Time-travel: go forward one state in history.

        Returns:
            True if redo was successful, False if at end of history
        """
        with self._lock:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self._state = self._history[self._history_index]
                self._notify_all_subscribers()
                return True
            return False

    def can_undo(self) -> bool:
        """Check if undo is possible."""
        with self._lock:
            return self._history_index > 0

    def can_redo(self) -> bool:
        """Check if redo is possible."""
        with self._lock:
            return self._history_index < len(self._history) - 1

    def get_history_size(self) -> int:
        """Get the size of the state history."""
        with self._lock:
            return len(self._history)

    def clear_history(self) -> None:
        """Clear state history (keeps current state)."""
        with self._lock:
            self._history = [self._state]
            self._history_index = 0

    def _notify_subscribers(self, changed_keys: Any) -> None:
        """
        Notify subscribers of state changes.

        Args:
            changed_keys: Keys that changed in the state update
        """
        # Map changed keys to events
        event_map = {
            "graph": StateEvent.GRAPH_CHANGED,
            "execution": [StateEvent.EXECUTION_STARTED, StateEvent.EXECUTION_STEP],
            "canvas": [StateEvent.SELECTION_CHANGED, StateEvent.ZOOM_CHANGED],
            "theme": StateEvent.THEME_CHANGED,
            "file_path": [StateEvent.FILE_OPENED, StateEvent.FILE_SAVED],
        }

        # Always notify general state change
        self._notify_event(StateEvent.STATE_CHANGED, self._state)

        # Notify specific events based on changed keys
        for key in changed_keys:
            if key in event_map:
                events = event_map[key]
                if not isinstance(events, list):
                    events = [events]

                state_slice = getattr(self._state, key, None)
                for event in events:
                    self._notify_event(event, state_slice)

    def _notify_all_subscribers(self) -> None:
        """Notify all subscribers (used for undo/redo)."""
        self._notify_event(StateEvent.STATE_CHANGED, self._state)
        self._notify_event(StateEvent.GRAPH_CHANGED, self._state.graph)
        self._notify_event(StateEvent.EXECUTION_STARTED, self._state.execution)
        self._notify_event(StateEvent.SELECTION_CHANGED, self._state.canvas)
        self._notify_event(StateEvent.THEME_CHANGED, self._state.theme)

    def _notify_event(self, event: StateEvent, payload: Any) -> None:
        """
        Notify subscribers of a specific event.

        Args:
            event: The event to notify
            payload: The payload to send to subscribers
        """
        if event in self._subscribers:
            for callback in self._subscribers[event][
                :
            ]:  # Copy list to avoid modification during iteration
                try:
                    callback(payload)
                except Exception as e:
                    # Log error but don't crash
                    print(f"Error in state subscriber callback: {e}")


# Singleton instance
_store: StateStore = None


def get_store() -> StateStore:
    """
    Get the global state store singleton.

    Returns:
        The global StateStore instance

    Example:
        >>> store = get_store()
        >>> state = store.get_state()
    """
    global _store
    if _store is None:
        _store = StateStore()
    return _store
