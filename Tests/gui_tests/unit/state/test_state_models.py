"""
Unit tests for state models.

Tests the immutable state dataclasses.
"""

import pytest
from gui_framework.state.models import AppState, CanvasState, ExecutionState, ThemeState


class TestExecutionState:
    """Tests for ExecutionState dataclass."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        state = ExecutionState()
        
        assert state.is_running is False
        assert state.is_paused is False
        assert state.current_iteration == 0
        assert state.max_iterations == 1000
        assert state.speed_ms == 100
        assert state.processor_type == "concurrent"
        assert state.auto_prepare is True
    
    def test_custom_values(self):
        """Test setting custom values."""
        state = ExecutionState(
            is_running=True,
            current_iteration=42,
            max_iterations=500,
            processor_type="forward"
        )
        
        assert state.is_running is True
        assert state.current_iteration == 42
        assert state.max_iterations == 500
        assert state.processor_type == "forward"
    
    def test_immutability(self):
        """Test that ExecutionState is immutable."""
        state = ExecutionState()
        
        with pytest.raises(Exception):  # FrozenInstanceError
            state.is_running = True
    
    def test_equality(self):
        """Test equality comparison."""
        state1 = ExecutionState(is_running=True)
        state2 = ExecutionState(is_running=True)
        state3 = ExecutionState(is_running=False)
        
        assert state1 == state2
        assert state1 != state3


class TestCanvasState:
    """Tests for CanvasState dataclass."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        state = CanvasState()
        
        assert state.zoom_level == 1.0
        assert state.pan_x == 0.0
        assert state.pan_y == 0.0
        assert state.selected_nodes == ()
        assert state.selected_edges == ()
        assert state.grid_visible is False
        assert state.grid_snap is False
    
    def test_custom_values(self):
        """Test setting custom values."""
        state = CanvasState(
            zoom_level=2.0,
            pan_x=100.0,
            pan_y=200.0,
            selected_nodes=("node1", "node2"),
            grid_visible=True
        )
        
        assert state.zoom_level == 2.0
        assert state.pan_x == 100.0
        assert state.pan_y == 200.0
        assert "node1" in state.selected_nodes
        assert "node2" in state.selected_nodes
        assert state.grid_visible is True
    
    def test_immutability(self):
        """Test that CanvasState is immutable."""
        state = CanvasState()
        
        with pytest.raises(Exception):
            state.zoom_level = 2.0
    
    def test_selected_nodes_tuple(self):
        """Test that selected_nodes is a tuple (immutable)."""
        state = CanvasState(selected_nodes=("node1", "node2"))
        
        assert isinstance(state.selected_nodes, tuple)
        # Tuples are immutable
        with pytest.raises(Exception):
            state.selected_nodes[0] = "node3"


class TestThemeState:
    """Tests for ThemeState dataclass."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        state = ThemeState()
        
        assert state.colors == {}
        assert state.fonts == {}
        assert state.current_theme == "default"
    
    def test_custom_values(self):
        """Test setting custom values."""
        colors = {"background": "#ffffff", "foreground": "#000000"}
        fonts = {"ui": "Arial 10"}
        state = ThemeState(
            colors=colors,
            fonts=fonts,
            current_theme="dark"
        )
        
        assert state.colors == colors
        assert state.fonts == fonts
        assert state.current_theme == "dark"
    
    def test_immutability(self):
        """Test that ThemeState is immutable."""
        state = ThemeState()
        
        with pytest.raises(Exception):
            state.current_theme = "light"


class TestAppState:
    """Tests for AppState dataclass."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        state = AppState()
        
        assert state.graph is None
        assert isinstance(state.execution, ExecutionState)
        assert isinstance(state.canvas, CanvasState)
        assert isinstance(state.theme, ThemeState)
        assert state.file_path is None
    
    def test_custom_values(self):
        """Test setting custom values."""
        execution = ExecutionState(is_running=True)
        canvas = CanvasState(zoom_level=2.0)
        theme = ThemeState(current_theme="dark")
        
        state = AppState(
            graph="test_graph",
            execution=execution,
            canvas=canvas,
            theme=theme,
            file_path="/path/to/file.drawio"
        )
        
        assert state.graph == "test_graph"
        assert state.execution == execution
        assert state.canvas == canvas
        assert state.theme == theme
        assert state.file_path == "/path/to/file.drawio"
    
    def test_immutability(self):
        """Test that AppState is immutable (except graph)."""
        state = AppState()
        
        # Cannot modify frozen fields
        with pytest.raises(Exception):
            state.file_path = "/new/path"
    
    def test_nested_state_access(self):
        """Test accessing nested state properties."""
        state = AppState(
            execution=ExecutionState(is_running=True),
            canvas=CanvasState(zoom_level=2.0)
        )
        
        assert state.execution.is_running is True
        assert state.canvas.zoom_level == 2.0
    
    def test_state_update_pattern(self):
        """Test the pattern for updating nested state."""
        state = AppState()
        
        # To update execution, create new ExecutionState
        new_execution = ExecutionState(
            **{**state.execution.__dict__, "is_running": True}
        )
        
        # Create new AppState with updated execution
        new_state = AppState(
            **{**state.__dict__, "execution": new_execution}
        )
        
        # Old state unchanged
        assert state.execution.is_running is False
        # New state updated
        assert new_state.execution.is_running is True
        # Other slices preserved
        assert new_state.canvas.zoom_level == state.canvas.zoom_level
