# Target GUI Architecture Design

## Executive Summary

This document defines the target MVVM (Model-View-ViewModel) architecture for the rebuilt ComputationalGraphs GUI. The design prioritizes:
- **Testability**: Pure Python view-models separated from PyQt6 views
- **Modularity**: Plugin-based widget registry with clear boundaries
- **Maintainability**: Explicit event flow and state ownership
- **Backward Compatibility**: Adapter layers preserve existing APIs

## Architecture Pattern: MVVM with Event Bus

### Why MVVM?

The current GUI uses a controller pattern, which is already better than monolithic design. However, MVVM offers advantages:

1. **Better Testability**: ViewModels are pure Python (no PyQt), easy to unit test
2. **Clearer Separation**: Model (domain), ViewModel (state/logic), View (UI)
3. **Reactive Design**: Observable properties enable automatic UI updates
4. **Framework Independence**: ViewModels could work with different UI frameworks

### MVVM vs Current Controller Pattern

**Current State**:
```
┌─────────────┐
│ MainWindow  │ (View + some logic)
│  (~1080 LOC)│
└──────┬──────┘
       │
       ├─> 16 Controllers (mixed view/logic)
       │   ├─> ExecutionController
       │   ├─> FileIOController
       │   └─> ... (others)
       │
       ├─> GraphCanvas (2606 LOC, view+logic mixed)
       ├─> NodePalette
       └─> Graph (Model)
```

**Target State**:
```
┌──────────────────────────────────────────┐
│            Application Layer             │
│  ┌────────────────────────────────────┐  │
│  │     WindowManager (Singleton)      │  │
│  │   - Manages top-level windows      │  │
│  │   - Lifecycle coordination         │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼─────────┐
│  Event Bus     │    │  State Store     │
│  (PubSub)      │    │  (Observable)    │
│  - Loose       │◄───┤  - Centralized   │
│    coupling    │    │  - Immutable     │
│  - Async       │    │  - History       │
└────────────────┘    └──────────────────┘
        ▲                      ▲
        │                      │
┌───────┴──────────────────────┴───────┐
│         ViewModel Layer              │
│  ┌─────────────┐  ┌──────────────┐  │
│  │ Canvas VM   │  │ Palette VM   │  │
│  │ (Pure Py)   │  │ (Pure Py)    │  │
│  ├─────────────┤  ├──────────────┤  │
│  │ Execution   │  │ FileIO VM    │  │
│  │ VM          │  │              │  │
│  └─────────────┘  └──────────────┘  │
└───────┬──────────────────────────────┘
        │
┌───────▼──────────────────────────────┐
│           View Layer (PyQt6)         │
│  ┌─────────────┐  ┌──────────────┐  │
│  │ CanvasView  │  │ PaletteView  │  │
│  │ (QGraphics  │  │ (QWidget)    │  │
│  │  Scene)     │  │              │  │
│  ├─────────────┤  ├──────────────┤  │
│  │ ControlView │  │ DialogViews  │  │
│  │             │  │              │  │
│  └─────────────┘  └──────────────┘  │
└──────────────────────────────────────┘
        │
┌───────▼──────────────────────────────┐
│          Model Layer (Domain)        │
│  ┌────────────────────────────────┐  │
│  │  Graph (existing)              │  │
│  │  Node (existing)               │  │
│  │  GraphProcessor (existing)     │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

## Component Design

### 1. State Store (Central State Management)

**Purpose**: Single source of truth for application state.

**Design**: Inspired by Redux/Vuex patterns.

```python
# gui_framework/state/store.py

from dataclasses import dataclass, field
from typing import Dict, Any, Callable, List
from enum import Enum

class StateEvent(Enum):
    """Events triggered by state changes"""
    GRAPH_CHANGED = "graph_changed"
    SELECTION_CHANGED = "selection_changed"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PAUSED = "execution_paused"
    THEME_CHANGED = "theme_changed"
    # ... more events

@dataclass(frozen=True)
class ExecutionState:
    """Immutable execution state"""
    is_running: bool = False
    is_paused: bool = False
    current_iteration: int = 0
    max_iterations: int = 1000
    speed_ms: int = 100
    processor_type: str = "concurrent"

@dataclass(frozen=True)
class CanvasState:
    """Immutable canvas state"""
    zoom_level: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    selected_nodes: List[str] = field(default_factory=list)
    selected_edges: List[tuple] = field(default_factory=list)

@dataclass(frozen=True)
class AppState:
    """Complete immutable application state"""
    graph: Any = None  # Graph model
    execution: ExecutionState = field(default_factory=ExecutionState)
    canvas: CanvasState = field(default_factory=CanvasState)
    theme: Dict[str, Any] = field(default_factory=dict)
    # ... more state slices

class StateStore:
    """
    Central state store with immutable state and time-travel debugging.
    Thread-safe for GUI updates.
    """
    def __init__(self):
        self._state: AppState = AppState()
        self._history: List[AppState] = [self._state]
        self._history_index: int = 0
        self._subscribers: Dict[StateEvent, List[Callable]] = {}

    def get_state(self) -> AppState:
        """Get current immutable state snapshot"""
        return self._state

    def update(self, **changes) -> None:
        """
        Update state immutably.
        Example: store.update(execution=ExecutionState(is_running=True))
        """
        # Create new state with changes (immutable update)
        new_state = self._state.__class__(
            **{**self._state.__dict__, **changes}
        )
        self._state = new_state

        # Add to history (for time-travel debugging)
        self._history = self._history[:self._history_index + 1]
        self._history.append(new_state)
        self._history_index += 1

        # Notify subscribers
        self._notify_subscribers(changes.keys())

    def subscribe(self, event: StateEvent, callback: Callable) -> None:
        """Subscribe to state changes"""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)

    def undo(self) -> bool:
        """Time-travel: go back one state"""
        if self._history_index > 0:
            self._history_index -= 1
            self._state = self._history[self._history_index]
            self._notify_all_subscribers()
            return True
        return False

    def redo(self) -> bool:
        """Time-travel: go forward one state"""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._state = self._history[self._history_index]
            self._notify_all_subscribers()
            return True
        return False

# Singleton access
_store = None

def get_store() -> StateStore:
    global _store
    if _store is None:
        _store = StateStore()
    return _store
```

**Key Features**:
- Immutable state (dataclasses with `frozen=True`)
- Time-travel debugging (undo/redo through history)
- Event-based subscriptions
- Thread-safe for GUI updates
- Testable without GUI

### 2. Event Bus (Loose Coupling)

**Purpose**: Decouple components through publish-subscribe pattern.

```python
# gui_framework/events/bus.py

from typing import Callable, Dict, List, Any
from enum import Enum
from dataclasses import dataclass

class EventType(Enum):
    """System-wide events"""
    # UI Events
    NODE_CREATED = "node_created"
    NODE_DELETED = "node_deleted"
    NODE_SELECTED = "node_selected"
    EDGE_CREATED = "edge_created"

    # Execution Events
    EXECUTION_STEP_COMPLETE = "execution_step_complete"
    GRAPH_RESET = "graph_reset"

    # File Events
    GRAPH_LOADED = "graph_loaded"
    GRAPH_SAVED = "graph_saved"

    # Theme Events
    THEME_UPDATED = "theme_updated"

@dataclass
class Event:
    """Event with payload"""
    type: EventType
    payload: Any = None
    sender: str = ""

class EventBus:
    """
    Global event bus for loose coupling between components.
    Async event handling for non-blocking UI.
    """
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_queue: List[Event] = []

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to event"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Unsubscribe from event"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: Event) -> None:
        """Publish event (synchronous)"""
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                callback(event)

    def publish_async(self, event: Event) -> None:
        """Queue event for async processing"""
        self._event_queue.append(event)

    def process_queue(self) -> None:
        """Process queued events (call from main loop)"""
        while self._event_queue:
            event = self._event_queue.pop(0)
            self.publish(event)

# Singleton access
_bus = None

def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
```

### 3. ViewModel Base Class

**Purpose**: Base class for all view-models with common patterns.

```python
# gui_framework/viewmodels/base.py

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List
from gui_framework.state.store import get_store, StateEvent
from gui_framework.events.bus import get_event_bus, EventType

class ObservableProperty:
    """Property descriptor for observable properties"""
    def __init__(self, name: str, default: Any = None):
        self.name = f"_{name}"
        self.default = default
        self.observers: List[Callable] = []

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.name, self.default)

    def __set__(self, obj, value):
        old_value = getattr(obj, self.name, self.default)
        setattr(obj, self.name, value)
        # Notify observers
        for observer in self.observers:
            observer(old_value, value)

class BaseViewModel(ABC):
    """
    Base class for all view-models.
    Pure Python, no PyQt dependencies.
    """
    def __init__(self):
        self._store = get_store()
        self._event_bus = get_event_bus()
        self._property_observers: Dict[str, List[Callable]] = {}

    def observe_property(self, prop_name: str, callback: Callable) -> None:
        """Observe property changes (for view binding)"""
        if prop_name not in self._property_observers:
            self._property_observers[prop_name] = []
        self._property_observers[prop_name].append(callback)

    def notify_property_changed(self, prop_name: str, old_value: Any, new_value: Any) -> None:
        """Notify observers of property change"""
        if prop_name in self._property_observers:
            for callback in self._property_observers[prop_name]:
                callback(old_value, new_value)

    @abstractmethod
    def initialize(self) -> None:
        """Initialize view-model (called after construction)"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources (called before destruction)"""
        pass

class CanvasViewModel(BaseViewModel):
    """Example: Canvas view-model"""

    zoom_level = ObservableProperty("zoom_level", 1.0)

    def __init__(self):
        super().__init__()
        self.selected_nodes: List[str] = []

    def initialize(self) -> None:
        # Subscribe to state changes
        self._store.subscribe(StateEvent.SELECTION_CHANGED,
                            self._on_selection_changed)

    def cleanup(self) -> None:
        # Unsubscribe (if needed)
        pass

    def select_node(self, node_id: str) -> None:
        """User action: select node"""
        self.selected_nodes.append(node_id)
        # Update central state
        state = self._store.get_state()
        self._store.update(
            canvas=state.canvas.__class__(
                **{**state.canvas.__dict__,
                   "selected_nodes": self.selected_nodes}
            )
        )
        # Publish event
        self._event_bus.publish(Event(EventType.NODE_SELECTED, node_id))

    def _on_selection_changed(self, state_slice: Any) -> None:
        """React to selection change from other sources"""
        # Update local state if needed
        pass
```

### 4. View Base Class (Adapter Pattern)

**Purpose**: Connect PyQt6 views to pure Python view-models.

```python
# gui_framework/views/base.py

from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QWidget
from gui_framework.viewmodels.base import BaseViewModel

class BaseView(QWidget, ABC):
    """
    Base class for all PyQt6 views.
    Binds to view-model for logic.
    """
    def __init__(self, viewmodel: BaseViewModel, parent=None):
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._bind_viewmodel()

    @abstractmethod
    def _bind_viewmodel(self) -> None:
        """
        Bind view to view-model properties.
        Called once during construction.
        """
        pass

    @abstractmethod
    def _setup_ui(self) -> None:
        """Setup PyQt UI (called after binding)"""
        pass

    def showEvent(self, event):
        """View becomes visible"""
        super().showEvent(event)
        self._viewmodel.initialize()

    def closeEvent(self, event):
        """View closes"""
        self._viewmodel.cleanup()
        super().closeEvent(event)

class CanvasView(BaseView):
    """Example: Canvas view"""

    def __init__(self, viewmodel: CanvasViewModel, parent=None):
        super().__init__(viewmodel, parent)
        self._setup_ui()

    def _bind_viewmodel(self) -> None:
        """Bind to view-model"""
        # Observe zoom changes
        self._viewmodel.observe_property("zoom_level",
                                        self._on_zoom_changed)

    def _setup_ui(self) -> None:
        """Setup PyQt UI"""
        # Create QGraphicsScene, etc.
        pass

    def _on_zoom_changed(self, old_value: float, new_value: float) -> None:
        """React to zoom change"""
        # Update QGraphicsView transform
        pass
```

### 5. Widget Registry (Plugin System)

**Purpose**: Extensible plugin system for registering new widgets.

```python
# gui_framework/registry/widget_registry.py

from typing import Dict, Type, Callable
from gui_framework.viewmodels.base import BaseViewModel
from gui_framework.views.base import BaseView

class WidgetRegistry:
    """
    Registry for view-model and view pairs.
    Enables plugin-based extension.
    """
    def __init__(self):
        self._viewmodels: Dict[str, Type[BaseViewModel]] = {}
        self._views: Dict[str, Type[BaseView]] = {}
        self._factories: Dict[str, Callable] = {}

    def register_widget(self,
                       name: str,
                       viewmodel_cls: Type[BaseViewModel],
                       view_cls: Type[BaseView],
                       factory: Callable = None) -> None:
        """Register a widget (ViewModel + View pair)"""
        self._viewmodels[name] = viewmodel_cls
        self._views[name] = view_cls
        if factory:
            self._factories[name] = factory

    def create_widget(self, name: str, **kwargs) -> tuple:
        """
        Create widget instance.
        Returns: (viewmodel, view) tuple
        """
        if name not in self._viewmodels:
            raise ValueError(f"Widget '{name}' not registered")

        # Use factory if provided
        if name in self._factories:
            return self._factories[name](**kwargs)

        # Default creation
        vm_cls = self._viewmodels[name]
        view_cls = self._views[name]
        viewmodel = vm_cls()
        view = view_cls(viewmodel, **kwargs)
        return viewmodel, view

    def get_registered_widgets(self) -> list:
        """Get list of registered widget names"""
        return list(self._viewmodels.keys())

# Singleton
_registry = None

def get_widget_registry() -> WidgetRegistry:
    global _registry
    if _registry is None:
        _registry = WidgetRegistry()
    return _registry
```

### 6. Window Manager

**Purpose**: Manage top-level windows and application lifecycle.

```python
# gui_framework/window/manager.py

from typing import Dict, Optional
from PyQt6.QtWidgets import QMainWindow, QApplication
from gui_framework.registry.widget_registry import get_widget_registry

class WindowManager:
    """
    Manages top-level windows and application lifecycle.
    Singleton coordinating all windows.
    """
    def __init__(self, app: QApplication):
        self._app = app
        self._windows: Dict[str, QMainWindow] = {}
        self._active_window: Optional[str] = None
        self._registry = get_widget_registry()

    def register_main_window(self, name: str, window: QMainWindow) -> None:
        """Register a main window"""
        self._windows[name] = window
        if self._active_window is None:
            self._active_window = name

    def show_window(self, name: str) -> None:
        """Show a registered window"""
        if name in self._windows:
            self._windows[name].show()
            self._active_window = name

    def close_window(self, name: str) -> None:
        """Close a registered window"""
        if name in self._windows:
            self._windows[name].close()
            del self._windows[name]
            if self._active_window == name:
                self._active_window = None

    def get_active_window(self) -> Optional[QMainWindow]:
        """Get currently active window"""
        if self._active_window:
            return self._windows.get(self._active_window)
        return None

    def shutdown(self) -> None:
        """Shutdown application"""
        for window in self._windows.values():
            window.close()
        self._app.quit()

# Singleton
_manager = None

def get_window_manager(app: QApplication = None) -> WindowManager:
    global _manager
    if _manager is None and app is not None:
        _manager = WindowManager(app)
    return _manager
```

## Threading Model

### Execution Model

**Problem**: Graph execution can be long-running and must not block GUI.

**Solution**: Worker thread pattern with Qt signals.

```python
# gui_framework/execution/worker.py

from PyQt6.QtCore import QThread, pyqtSignal
from zorvan.Core.GraphProcessor import GraphProcessor

class ExecutionWorker(QThread):
    """
    Worker thread for graph execution.
    Emits signals for progress updates.
    """
    step_completed = pyqtSignal(int)  # iteration number
    execution_finished = pyqtSignal()
    execution_error = pyqtSignal(str)  # error message

    def __init__(self, graph, processor_type: str, max_iterations: int):
        super().__init__()
        self.graph = graph
        self.processor_type = processor_type
        self.max_iterations = max_iterations
        self._stop_requested = False

    def run(self):
        """Execute in worker thread"""
        try:
            processor = GraphProcessor(self.graph)

            for i in range(self.max_iterations):
                if self._stop_requested:
                    break

                # Execute one step
                if self.processor_type == "concurrent":
                    processor.ComputeGraph(iterations=1)
                else:
                    processor.ForwardProcessing(iterations=1)

                # Emit progress
                self.step_completed.emit(i + 1)

            self.execution_finished.emit()

        except Exception as e:
            self.execution_error.emit(str(e))

    def stop(self):
        """Request stop"""
        self._stop_requested = True
```

**Thread Safety Rules**:
1. **State Store**: Only update from main GUI thread
2. **Event Bus**: Publish from any thread, process in main thread
3. **Worker Threads**: Use Qt signals to communicate with GUI
4. **Graph Model**: Read-only from worker threads (or use locks)

## File Structure

```
ComputationalGraphs/
├── gui_framework/              # New MVVM framework
│   ├── __init__.py
│   ├── state/                  # State management
│   │   ├── __init__.py
│   │   ├── store.py           # StateStore
│   │   └── models.py          # State dataclasses
│   ├── events/                 # Event bus
│   │   ├── __init__.py
│   │   └── bus.py
│   ├── viewmodels/             # Pure Python view-models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── canvas_vm.py
│   │   ├── palette_vm.py
│   │   ├── execution_vm.py
│   │   └── ...
│   ├── views/                  # PyQt6 views
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── canvas_view.py
│   │   ├── palette_view.py
│   │   └── ...
│   ├── registry/               # Widget registry
│   │   ├── __init__.py
│   │   └── widget_registry.py
│   ├── window/                 # Window management
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── execution/              # Execution threading
│   │   ├── __init__.py
│   │   └── worker.py
│   └── adapters/               # Backward compatibility
│       ├── __init__.py
│       └── legacy_adapter.py
│
├── GUI/                        # Existing GUI (to be migrated)
│   ├── main_window.py         # Keep during migration
│   ├── graph_canvas.py        # Migrate to views/
│   ├── node_palette.py        # Migrate to views/
│   ├── controllers/           # Migrate logic to viewmodels/
│   └── ...
│
├── gui_tests/                  # New test structure
│   ├── unit/                   # Unit tests (no GUI)
│   │   ├── test_state_store.py
│   │   ├── test_event_bus.py
│   │   ├── test_canvas_vm.py
│   │   └── ...
│   ├── integration/            # Integration tests (headless)
│   │   ├── test_canvas_integration.py
│   │   └── ...
│   └── smoke/                  # Smoke tests
│       └── test_app_launch.py
│
└── Tests/                      # Existing tests (keep)
    └── ...
```

## Migration Strategy

### Phase 1: Foundation (Week 1)
1. Create `gui_framework/` module structure
2. Implement StateStore with tests
3. Implement EventBus with tests
4. Implement base ViewModel and View classes
5. Implement WidgetRegistry
6. Implement WindowManager

**Deliverable**: Core framework with unit tests (no GUI dependencies yet)

### Phase 2: Proof of Concept (Week 1-2)
1. Port CollapsibleSection as first widget
2. Port ConsoleController → ConsoleViewModel + ConsoleView
3. Create adapter for old MainWindow to use new widgets
4. Write integration test demonstrating new pattern

**Deliverable**: One working widget in new framework, integrated with old GUI

### Phase 3: Core Widgets (Week 2-4)
1. Port NodePalette (high value, moderate complexity)
2. Port Execution controls (high value, low complexity)
3. Port Theme manager into StateStore
4. Update examples to use new framework

**Deliverable**: 3 critical widgets migrated, theme system unified

### Phase 4: Canvas (Week 4-5)
1. Extract canvas logic into CanvasViewModel
2. Create CanvasView with QGraphicsScene
3. Migrate node/edge rendering
4. Migrate interaction (drag, select, connect)
5. Extensive integration tests

**Deliverable**: Canvas working in new framework

### Phase 5: Remaining Components (Week 5-7)
1. Dialogs (MLP, Backprop, NodeEditor, etc.)
2. File I/O controller → ViewModel
3. Layout algorithms integration
4. Plotting windows
5. Advanced features (undo/redo, clipboard)

**Deliverable**: Feature parity with old GUI

### Phase 6: Polish (Week 7-8)
1. Remove old GUI code
2. Remove adapters
3. Performance optimization
4. Documentation
5. Final testing and release

**Deliverable**: Production-ready new GUI

## Backward Compatibility Strategy

### Adapter Pattern

Existing code that depends on old GUI APIs will use adapters:

```python
# gui_framework/adapters/legacy_adapter.py

from zorvan.GUI.main_window import MainWindow as OldMainWindow
from gui_framework.window.manager import get_window_manager

class LegacyMainWindowAdapter:
    """
    Adapter to make new GUI compatible with code expecting old MainWindow.
    Provides same API surface as old MainWindow.
    """
    def __init__(self):
        self._window_manager = get_window_manager()
        self._main_window = self._window_manager.get_active_window()

    def set_graph(self, graph):
        """Old API: set graph"""
        # Delegate to new StateStore
        from gui_framework.state.store import get_store
        store = get_store()
        store.update(graph=graph)

    # ... other adapter methods
```

### Feature Flags

Enable gradual rollout:

```python
# config.py

USE_NEW_GUI = False  # Feature flag

if USE_NEW_GUI:
    from gui_framework.views.canvas_view import CanvasView as Canvas
else:
    from zorvan.GUI.graph_canvas import GraphCanvas as Canvas
```

## Testing Strategy

### Unit Tests (No GUI)

Test view-models without PyQt:

```python
# gui_tests/unit/test_canvas_vm.py

import pytest
from gui_framework.viewmodels.canvas_vm import CanvasViewModel

def test_select_node_updates_state():
    vm = CanvasViewModel()
    vm.initialize()

    vm.select_node("node1")

    assert "node1" in vm.selected_nodes
    # Verify state store updated
    from gui_framework.state.store import get_store
    state = get_store().get_state()
    assert "node1" in state.canvas.selected_nodes
```

### Integration Tests (Headless)

Test with PyQt in offscreen mode:

```python
# gui_tests/integration/test_canvas_integration.py

import pytest
from PyQt6.QtWidgets import QApplication
from gui_framework.views.canvas_view import CanvasView
from gui_framework.viewmodels.canvas_vm import CanvasViewModel

@pytest.fixture
def qapp():
    import os
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_canvas_node_creation(qapp):
    vm = CanvasViewModel()
    view = CanvasView(vm)

    # Simulate node creation
    vm.create_node("AdditionNode", x=100, y=100)

    # Verify node appears in view
    # ...
```

### Smoke Tests

Quick sanity check:

```python
# gui_tests/smoke/test_app_launch.py

def test_app_launches():
    """Smoke test: app launches without crashing"""
    from gui_framework.window.manager import get_window_manager
    from PyQt6.QtWidgets import QApplication
    import os
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'

    app = QApplication([])
    manager = get_window_manager(app)

    # Should not crash
    assert manager is not None
```

## CI Configuration

### GitHub Actions Workflow

```yaml
# .github/workflows/gui-tests.yml

name: GUI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          xvfb \
          libxkbcommon-x11-0 \
          libxcb-icccm4 \
          libxcb-image0 \
          libxcb-keysyms1 \
          libxcb-randr0 \
          libxcb-render-util0 \
          libxcb-xinerama0 \
          libxcb-xfixes0 \
          libegl1 \
          libgl1 \
          libdbus-1-3

    - name: Install Python dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements_gui.txt
        pip install -r requirements_dev.txt
        pip install -e .

    - name: Run unit tests (no GUI)
      run: |
        pytest gui_tests/unit/ -v

    - name: Run integration tests (headless)
      run: |
        export QT_QPA_PLATFORM=offscreen
        export QT_DEBUG_PLUGINS=0
        pytest gui_tests/integration/ -v

    - name: Run smoke tests
      run: |
        export QT_QPA_PLATFORM=offscreen
        timeout 30s pytest gui_tests/smoke/ -v || exit 0
```

## Performance Considerations

### Optimization Targets

1. **Canvas Rendering**: Use QGraphicsScene with cached rendering
2. **State Updates**: Batch updates to minimize redraws
3. **Event Bus**: Async event processing to avoid blocking
4. **Large Graphs**: Virtual scrolling and level-of-detail rendering

### Profiling

```python
# gui_framework/profiling/profiler.py

import cProfile
import pstats
from functools import wraps

def profile_method(func):
    """Decorator to profile method performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10
        return result
    return wrapper
```

## Accessibility

### Requirements

1. **Keyboard Navigation**: All features accessible via keyboard
2. **Screen Reader**: Proper ARIA labels (Qt Accessible)
3. **High Contrast**: Theme support for high contrast modes
4. **Scalable UI**: Font size adjustments

### Implementation

```python
# views/accessible_view.py

from PyQt6.QtCore import Qt

class AccessibleView(BaseView):
    """Base class with accessibility features"""

    def _setup_accessibility(self):
        """Setup accessibility features"""
        # Set accessible name/description
        self.setAccessibleName("Graph Canvas")
        self.setAccessibleDescription("Interactive computational graph editor")

        # Enable keyboard focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Set role
        # Qt automatically handles screen readers
```

## Documentation Requirements

### Generated Documentation

Use Sphinx with autodoc:

```python
# gui_framework/viewmodels/canvas_vm.py

class CanvasViewModel(BaseViewModel):
    """
    View-model for the graph canvas.

    Manages canvas state including:
    - Node/edge selection
    - Zoom and pan
    - Clipboard operations

    Example:
        >>> vm = CanvasViewModel()
        >>> vm.initialize()
        >>> vm.select_node("node1")
        >>> vm.zoom_level = 1.5

    Attributes:
        zoom_level (float): Current zoom level (1.0 = 100%)
        selected_nodes (List[str]): List of selected node IDs
    """
```

### API Documentation

Auto-generate with:
```bash
cd docs
sphinx-apidoc -f -o source/api ../gui_framework
make html
```

## Security Considerations

### Input Validation

All user inputs must be validated in view-models:

```python
def set_max_iterations(self, value: int) -> None:
    """Set maximum iterations (validated)"""
    if not isinstance(value, int):
        raise TypeError("Max iterations must be integer")
    if value < 1 or value > 1000000:
        raise ValueError("Max iterations must be 1-1000000")
    self._max_iterations = value
```

### File Operations

Sanitize file paths to prevent path traversal:

```python
import os
from pathlib import Path

def safe_file_path(user_path: str) -> Path:
    """Validate and sanitize file path"""
    path = Path(user_path).resolve()
    # Ensure within allowed directory
    if not str(path).startswith(str(ALLOWED_DIR)):
        raise ValueError("Invalid file path")
    return path
```

## Summary

This MVVM architecture provides:

✅ **Testability**: Pure Python view-models, no GUI in unit tests
✅ **Modularity**: Plugin registry, clear boundaries
✅ **Maintainability**: Explicit state flow, event-driven
✅ **Backward Compatibility**: Adapter pattern preserves old APIs
✅ **Performance**: Worker threads, optimized rendering
✅ **Accessibility**: Keyboard navigation, screen reader support

Next steps:
1. Review and approve this architecture
2. Begin Phase 1: Foundation implementation
3. Create proof-of-concept widget
4. Iterate based on feedback
