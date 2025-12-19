"""
Immutable state models for the application.

All state classes use frozen dataclasses to ensure immutability.
State updates create new instances rather than modifying existing ones.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class ExecutionState:
    """
    Immutable execution state.
    
    Attributes:
        is_running: Whether graph execution is currently running
        is_paused: Whether execution is paused
        current_iteration: Current iteration number
        max_iterations: Maximum number of iterations
        speed_ms: Execution speed in milliseconds per step
        processor_type: Type of processor ("concurrent" or "forward")
        auto_prepare: Whether to auto-prepare forward processing
    """
    is_running: bool = False
    is_paused: bool = False
    current_iteration: int = 0
    max_iterations: int = 1000
    speed_ms: int = 100
    processor_type: str = "concurrent"
    auto_prepare: bool = True


@dataclass(frozen=True)
class CanvasState:
    """
    Immutable canvas state.
    
    Attributes:
        zoom_level: Current zoom level (1.0 = 100%)
        pan_x: Horizontal pan offset
        pan_y: Vertical pan offset
        selected_nodes: List of selected node IDs
        selected_edges: List of selected edge tuples (from_id, to_id)
        grid_visible: Whether grid is visible
        grid_snap: Whether grid snapping is enabled
    """
    zoom_level: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    selected_nodes: Tuple[str, ...] = field(default_factory=tuple)
    selected_edges: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    grid_visible: bool = False
    grid_snap: bool = False


@dataclass(frozen=True)
class ThemeState:
    """
    Immutable theme state.
    
    Attributes:
        colors: Dictionary of color name to hex color value
        fonts: Dictionary of font name to font family/size
        current_theme: Name of current theme
    """
    colors: Dict[str, str] = field(default_factory=dict)
    fonts: Dict[str, str] = field(default_factory=dict)
    current_theme: str = "default"


@dataclass(frozen=True)
class AppState:
    """
    Complete immutable application state.
    
    This is the root state object containing all application state slices.
    
    Attributes:
        graph: The computational graph model (not frozen)
        execution: Execution state slice
        canvas: Canvas state slice
        theme: Theme state slice
        file_path: Current file path (None if unsaved)
    """
    graph: Any = None
    execution: ExecutionState = field(default_factory=ExecutionState)
    canvas: CanvasState = field(default_factory=CanvasState)
    theme: ThemeState = field(default_factory=ThemeState)
    file_path: str = None
