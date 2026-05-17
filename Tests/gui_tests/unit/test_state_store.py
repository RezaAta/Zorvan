"""
Unit tests for state store.

Tests the StateStore implementation including immutability,
subscriptions, and time-travel debugging.
"""

import pytest
from gui_framework.state.models import AppState, CanvasState, ExecutionState
from gui_framework.state.store import StateEvent, StateStore, get_store


class TestStateStore:
    """Tests for StateStore class."""
    
    def test_store_initialization(self):
        """Test that store initializes with empty state."""
        store = StateStore()
        state = store.get_state()
        
        assert isinstance(state, AppState)
        assert state.graph is None
        assert state.execution.is_running is False
        assert state.canvas.zoom_level == 1.0
    
    def test_state_immutability(self):
        """Test that state objects are immutable."""
        store = StateStore()
        state = store.get_state()
        
        # Attempt to modify should raise error
        with pytest.raises(Exception):  # FrozenInstanceError
            state.execution.is_running = True
    
    def test_update_creates_new_state(self):
        """Test that update creates new state object."""
        store = StateStore()
        old_state = store.get_state()
        
        new_execution = ExecutionState(is_running=True)
        store.update(execution=new_execution)
        
        new_state = store.get_state()
        
        # States should be different objects
        assert old_state is not new_state
        # Old state unchanged
        assert old_state.execution.is_running is False
        # New state has changes
        assert new_state.execution.is_running is True
    
    def test_update_preserves_other_slices(self):
        """Test that updating one slice preserves others."""
        store = StateStore()
        
        # Set initial canvas state
        initial_canvas = CanvasState(zoom_level=2.0)
        store.update(canvas=initial_canvas)
        
        # Update execution
        new_execution = ExecutionState(is_running=True)
        store.update(execution=new_execution)
        
        state = store.get_state()
        
        # Canvas should be preserved
        assert state.canvas.zoom_level == 2.0
        # Execution should be updated
        assert state.execution.is_running is True
    
    def test_subscribe_callback_called(self):
        """Test that subscribers are notified of changes."""
        store = StateStore()
        callback_called = []
        
        def callback(state_slice):
            callback_called.append(state_slice)
        
        store.subscribe(StateEvent.STATE_CHANGED, callback)
        store.update(execution=ExecutionState(is_running=True))
        
        assert len(callback_called) == 1
        assert isinstance(callback_called[0], AppState)
    
    def test_subscribe_specific_event(self):
        """Test subscribing to specific state events."""
        store = StateStore()
        execution_callbacks = []
        
        def on_execution(state_slice):
            execution_callbacks.append(state_slice)
        
        store.subscribe(StateEvent.EXECUTION_STARTED, on_execution)
        store.update(execution=ExecutionState(is_running=True))
        
        assert len(execution_callbacks) > 0
    
    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        store = StateStore()
        callback_called = []
        
        def callback(state_slice):
            callback_called.append(state_slice)
        
        store.subscribe(StateEvent.STATE_CHANGED, callback)
        store.update(execution=ExecutionState(is_running=True))
        assert len(callback_called) == 1
        
        # Unsubscribe
        store.unsubscribe(StateEvent.STATE_CHANGED, callback)
        store.update(execution=ExecutionState(is_running=False))
        
        # Should not be called again
        assert len(callback_called) == 1
    
    def test_history_tracking(self):
        """Test that state history is tracked."""
        store = StateStore()
        
        assert store.get_history_size() == 1
        
        store.update(execution=ExecutionState(is_running=True))
        assert store.get_history_size() == 2
        
        store.update(execution=ExecutionState(is_running=False))
        assert store.get_history_size() == 3
    
    def test_undo(self):
        """Test undo functionality."""
        store = StateStore()
        
        # Make changes
        store.update(execution=ExecutionState(is_running=True))
        assert store.get_state().execution.is_running is True
        
        # Undo
        result = store.undo()
        assert result is True
        assert store.get_state().execution.is_running is False
    
    def test_undo_at_beginning(self):
        """Test that undo at beginning returns False."""
        store = StateStore()
        
        result = store.undo()
        assert result is False
    
    def test_redo(self):
        """Test redo functionality."""
        store = StateStore()
        
        # Make changes
        store.update(execution=ExecutionState(is_running=True))
        
        # Undo
        store.undo()
        assert store.get_state().execution.is_running is False
        
        # Redo
        result = store.redo()
        assert result is True
        assert store.get_state().execution.is_running is True
    
    def test_redo_at_end(self):
        """Test that redo at end returns False."""
        store = StateStore()
        
        result = store.redo()
        assert result is False
    
    def test_can_undo_redo(self):
        """Test can_undo and can_redo methods."""
        store = StateStore()
        
        assert store.can_undo() is False
        assert store.can_redo() is False
        
        store.update(execution=ExecutionState(is_running=True))
        assert store.can_undo() is True
        assert store.can_redo() is False
        
        store.undo()
        assert store.can_undo() is False
        assert store.can_redo() is True
    
    def test_update_after_undo_clears_future(self):
        """Test that update after undo clears future history."""
        store = StateStore()
        
        # Create history: A -> B -> C
        store.update(execution=ExecutionState(current_iteration=1))
        store.update(execution=ExecutionState(current_iteration=2))
        assert store.get_history_size() == 3
        
        # Undo to B
        store.undo()
        assert store.get_state().execution.current_iteration == 1
        
        # Update creates D, clearing C
        store.update(execution=ExecutionState(current_iteration=3))
        
        # Can't redo to C anymore
        assert store.can_redo() is False
        assert store.get_state().execution.current_iteration == 3
    
    def test_history_limit(self):
        """Test that history is limited to max size."""
        store = StateStore()
        max_history = store._max_history
        
        # Create more history than limit
        for i in range(max_history + 10):
            store.update(execution=ExecutionState(current_iteration=i))
        
        # History should be capped
        assert store.get_history_size() <= max_history
    
    def test_clear_history(self):
        """Test clearing state history."""
        store = StateStore()
        
        store.update(execution=ExecutionState(is_running=True))
        store.update(execution=ExecutionState(is_running=False))
        assert store.get_history_size() > 1
        
        store.clear_history()
        assert store.get_history_size() == 1
        assert store.can_undo() is False
    
    def test_multiple_updates_in_sequence(self):
        """Test multiple updates maintain consistency."""
        store = StateStore()
        
        store.update(execution=ExecutionState(is_running=True))
        store.update(canvas=CanvasState(zoom_level=2.0))
        store.update(file_path="/path/to/file.drawio")
        
        state = store.get_state()
        assert state.execution.is_running is True
        assert state.canvas.zoom_level == 2.0
        assert state.file_path == "/path/to/file.drawio"
    
    def test_callback_error_handling(self):
        """Test that callback errors don't crash the store."""
        store = StateStore()
        
        def bad_callback(state_slice):
            raise ValueError("Test error")
        
        store.subscribe(StateEvent.STATE_CHANGED, bad_callback)
        
        # Should not raise, error should be caught
        store.update(execution=ExecutionState(is_running=True))
        
        # Store should still work
        assert store.get_state().execution.is_running is True


class TestGetStore:
    """Tests for get_store singleton."""
    
    def test_get_store_returns_instance(self):
        """Test that get_store returns a StateStore instance."""
        store = get_store()
        assert isinstance(store, StateStore)
    
    def test_get_store_returns_same_instance(self):
        """Test that get_store returns the same singleton."""
        store1 = get_store()
        store2 = get_store()
        assert store1 is store2
    
    def test_singleton_persists_state(self):
        """Test that singleton persists state across calls."""
        store1 = get_store()
        store1.update(execution=ExecutionState(is_running=True))
        
        store2 = get_store()
        assert store2.get_state().execution.is_running is True


class TestStateEventNotifications:
    """Tests for state event notifications."""
    
    def test_graph_changed_event(self):
        """Test GRAPH_CHANGED event is triggered."""
        store = StateStore()
        callbacks = []
        
        store.subscribe(StateEvent.GRAPH_CHANGED, lambda s: callbacks.append(s))
        store.update(graph="test_graph")
        
        assert len(callbacks) > 0
    
    def test_execution_event(self):
        """Test execution events are triggered."""
        store = StateStore()
        callbacks = []
        
        store.subscribe(StateEvent.EXECUTION_STARTED, lambda s: callbacks.append(s))
        store.update(execution=ExecutionState(is_running=True))
        
        assert len(callbacks) > 0
    
    def test_theme_changed_event(self):
        """Test THEME_CHANGED event is triggered."""
        store = StateStore()
        callbacks = []
        
        from gui_framework.state.models import ThemeState
        store.subscribe(StateEvent.THEME_CHANGED, lambda s: callbacks.append(s))
        store.update(theme=ThemeState(current_theme="dark"))
        
        assert len(callbacks) > 0
