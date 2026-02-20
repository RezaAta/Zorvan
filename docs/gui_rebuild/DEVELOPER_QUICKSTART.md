# Developer Quickstart Guide - GUI Rebuild

## Overview

This guide helps developers get started with the new MVVM GUI architecture. Whether you're contributing to the migration or building new widgets, this document provides practical examples and best practices.

## Prerequisites

### Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/ORG_OR_USER/zorvan.git
cd zorvan

# 2. Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements_gui.txt
pip install -r requirements_dev.txt

# 4. Install package in editable mode
pip install -e .

# 5. Verify installation
python -c "import zorvan; print('✓ Core installed')"
python -c "from PyQt6.QtWidgets import QApplication; print('✓ PyQt6 installed')"
python -m pytest --version
```

### Running the Current GUI

```bash
# Launch GUI
python run_gui.py

# If you see libEGL errors on Linux:
export QT_QPA_PLATFORM=offscreen  # For headless testing
# Or install: sudo apt-get install libegl1 libgl1
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest gui_tests/unit/                    # Unit tests (no GUI)
pytest gui_tests/integration/             # Integration tests (headless)
pytest zorvan/Tests/MLPTests/  # Core MLP tests

# Run with coverage
pytest --cov=gui_framework --cov-report=html

# Run tests in headless mode (Linux)
export QT_QPA_PLATFORM=offscreen
pytest gui_tests/
```

## Architecture Quickstart

### The MVVM Pattern

```
User Action → View → ViewModel → State Store → Event Bus
                ↑                     ↓
                └─────── Notify ──────┘
```

**Key Principles**:
1. **Views** handle UI only (PyQt6 widgets)
2. **ViewModels** contain logic (pure Python, no PyQt)
3. **State Store** is single source of truth
4. **Event Bus** enables loose coupling

### Directory Structure

```
ComputationalGraphs/
├── gui_framework/              # NEW: MVVM framework
│   ├── state/                 # State management
│   │   ├── store.py          # StateStore singleton
│   │   └── models.py         # State dataclasses
│   ├── events/                # Event bus
│   │   └── bus.py            # EventBus singleton
│   ├── viewmodels/            # Pure Python logic
│   │   ├── base.py           # BaseViewModel
│   │   ├── canvas_vm.py      # Canvas logic
│   │   └── palette_vm.py     # Palette logic
│   ├── views/                 # PyQt6 UI
│   │   ├── base.py           # BaseView
│   │   ├── canvas_view.py    # Canvas UI
│   │   └── palette_view.py   # Palette UI
│   ├── registry/              # Widget registration
│   │   └── widget_registry.py
│   ├── window/                # Window management
│   │   └── manager.py
│   └── adapters/              # Backward compatibility
│       └── legacy_adapter.py
│
├── GUI/                       # EXISTING: Current GUI (being migrated)
│   ├── main_window.py        # Main window
│   ├── graph_canvas.py       # Canvas (to be migrated)
│   ├── node_palette.py       # Palette (to be migrated)
│   └── controllers/          # Controllers (logic to viewmodels)
│
└── gui_tests/                 # NEW: Tests for new framework
    ├── unit/                 # Unit tests (no PyQt)
    ├── integration/          # Integration tests (headless PyQt)
    └── smoke/                # Smoke tests
```

## Creating Your First Widget

### Example: Simple Counter Widget

#### Step 1: Create ViewModel (Pure Python)

```python
# gui_framework/viewmodels/counter_vm.py

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty
from gui_framework.events.bus import get_event_bus, Event, EventType

class CounterViewModel(BaseViewModel):
    """
    ViewModel for a simple counter widget.
    Pure Python, no PyQt dependencies - easily testable.
    """

    # Observable property - views will auto-update when this changes
    count = ObservableProperty("count", default=0)

    def __init__(self):
        super().__init__()
        self._max_count = 100

    def initialize(self) -> None:
        """Called when view is shown"""
        # Subscribe to events if needed
        pass

    def cleanup(self) -> None:
        """Called when view is closed"""
        # Cleanup resources
        pass

    def increment(self) -> None:
        """User action: increment counter"""
        if self.count < self._max_count:
            self.count += 1
            # Update state store
            self._update_state()
            # Publish event
            self._event_bus.publish(Event(
                type=EventType.CUSTOM,
                payload={"count": self.count}
            ))

    def decrement(self) -> None:
        """User action: decrement counter"""
        if self.count > 0:
            self.count -= 1
            self._update_state()

    def reset(self) -> None:
        """User action: reset counter"""
        self.count = 0
        self._update_state()

    def _update_state(self) -> None:
        """Update central state store"""
        # In real widget, update relevant state slice
        pass
```

#### Step 2: Write Tests (Before View!)

```python
# gui_tests/unit/test_counter_vm.py

import pytest
from gui_framework.viewmodels.counter_vm import CounterViewModel

def test_counter_increments():
    """Test counter increments correctly"""
    vm = CounterViewModel()
    vm.initialize()

    initial = vm.count
    vm.increment()

    assert vm.count == initial + 1

def test_counter_decrements():
    """Test counter decrements correctly"""
    vm = CounterViewModel()
    vm.count = 5

    vm.decrement()

    assert vm.count == 4

def test_counter_does_not_go_negative():
    """Test counter does not go below zero"""
    vm = CounterViewModel()
    vm.count = 0

    vm.decrement()

    assert vm.count == 0

def test_counter_respects_max():
    """Test counter does not exceed maximum"""
    vm = CounterViewModel()
    vm.count = 100

    vm.increment()

    assert vm.count == 100

def test_counter_reset():
    """Test counter resets to zero"""
    vm = CounterViewModel()
    vm.count = 42

    vm.reset()

    assert vm.count == 0

# Run tests: pytest gui_tests/unit/test_counter_vm.py -v
```

#### Step 3: Create View (PyQt6 UI)

```python
# gui_framework/views/counter_view.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from gui_framework.views.base import BaseView
from gui_framework.viewmodels.counter_vm import CounterViewModel

class CounterView(BaseView):
    """
    View for counter widget.
    Thin UI layer - all logic in ViewModel.
    """

    def __init__(self, viewmodel: CounterViewModel, parent=None):
        super().__init__(viewmodel, parent)
        self._setup_ui()

    def _bind_viewmodel(self) -> None:
        """Bind view to viewmodel properties"""
        # Observe count changes
        self._viewmodel.observe_property("count", self._on_count_changed)

    def _setup_ui(self) -> None:
        """Setup PyQt UI"""
        layout = QVBoxLayout(self)

        # Counter display
        self.label = QLabel("0")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.label.font()
        font.setPointSize(24)
        self.label.setFont(font)
        layout.addWidget(self.label)

        # Buttons
        button_layout = QHBoxLayout()

        self.decrement_btn = QPushButton("-")
        self.decrement_btn.clicked.connect(self._on_decrement_clicked)
        button_layout.addWidget(self.decrement_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(self.reset_btn)

        self.increment_btn = QPushButton("+")
        self.increment_btn.clicked.connect(self._on_increment_clicked)
        button_layout.addWidget(self.increment_btn)

        layout.addLayout(button_layout)

        # Initialize display
        self._update_display()

    def _on_count_changed(self, old_value: int, new_value: int) -> None:
        """React to count change from viewmodel"""
        self._update_display()

    def _update_display(self) -> None:
        """Update label with current count"""
        self.label.setText(str(self._viewmodel.count))

    # Event handlers - delegate to viewmodel
    def _on_increment_clicked(self) -> None:
        """Increment button clicked"""
        self._viewmodel.increment()

    def _on_decrement_clicked(self) -> None:
        """Decrement button clicked"""
        self._viewmodel.decrement()

    def _on_reset_clicked(self) -> None:
        """Reset button clicked"""
        self._viewmodel.reset()
```

#### Step 4: Register Widget

```python
# gui_framework/registry/widget_registry.py (add to existing)

from gui_framework.viewmodels.counter_vm import CounterViewModel
from gui_framework.views.counter_view import CounterView

# In initialization code:
registry = get_widget_registry()
registry.register_widget(
    name="counter",
    viewmodel_cls=CounterViewModel,
    view_cls=CounterView
)
```

#### Step 5: Use Widget

```python
# In your application code:
from gui_framework.registry.widget_registry import get_widget_registry

registry = get_widget_registry()
viewmodel, view = registry.create_widget("counter")

# Show the widget
view.show()
```

### Integration Test

```python
# gui_tests/integration/test_counter_integration.py

import pytest
from PyQt6.QtWidgets import QApplication
from gui_framework.viewmodels.counter_vm import CounterViewModel
from gui_framework.views.counter_view import CounterView

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests"""
    import os
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_counter_ui_updates(qapp):
    """Test that UI updates when viewmodel changes"""
    vm = CounterViewModel()
    view = CounterView(vm)

    # Increment through viewmodel
    vm.increment()

    # UI should update
    assert view.label.text() == "1"

def test_counter_button_clicks(qapp):
    """Test that button clicks update viewmodel"""
    vm = CounterViewModel()
    view = CounterView(vm)

    # Click increment button
    view.increment_btn.click()

    # Viewmodel should update
    assert vm.count == 1

    # UI should also update
    assert view.label.text() == "1"

# Run: QT_QPA_PLATFORM=offscreen pytest gui_tests/integration/test_counter_integration.py -v
```

## Working with State Store

### Reading State

```python
from gui_framework.state.store import get_store

store = get_store()
state = store.get_state()

# Access state properties
print(f"Current zoom: {state.canvas.zoom_level}")
print(f"Selected nodes: {state.canvas.selected_nodes}")
print(f"Execution running: {state.execution.is_running}")
```

### Updating State

```python
from gui_framework.state.store import get_store
from gui_framework.state.models import ExecutionState

store = get_store()

# Get current state
state = store.get_state()

# Create new execution state (immutable)
new_execution = ExecutionState(
    is_running=True,
    is_paused=False,
    current_iteration=0,
    max_iterations=1000,
    speed_ms=100
)

# Update store (creates new state)
store.update(execution=new_execution)
```

### Subscribing to State Changes

```python
from gui_framework.state.store import get_store, StateEvent

store = get_store()

def on_execution_changed(state_slice):
    """Called when execution state changes"""
    print(f"Execution state changed: {state_slice}")

# Subscribe
store.subscribe(StateEvent.EXECUTION_STARTED, on_execution_changed)

# Changes to execution state will trigger callback
```

## Working with Event Bus

### Publishing Events

```python
from gui_framework.events.bus import get_event_bus, Event, EventType

bus = get_event_bus()

# Publish node created event
bus.publish(Event(
    type=EventType.NODE_CREATED,
    payload={"node_id": "node_123", "node_type": "AdditionNode"},
    sender="CanvasViewModel"
))
```

### Subscribing to Events

```python
from gui_framework.events.bus import get_event_bus, EventType

bus = get_event_bus()

def on_node_created(event):
    """Handle node creation"""
    node_id = event.payload["node_id"]
    print(f"Node created: {node_id}")

# Subscribe
bus.subscribe(EventType.NODE_CREATED, on_node_created)
```

### Async Events

```python
# Publish async (queued for later processing)
bus.publish_async(Event(
    type=EventType.GRAPH_SAVED,
    payload={"filename": "graph.drawio"}
))

# Process queue (typically in main loop)
bus.process_queue()
```

## Common Patterns

### Pattern 1: User Action Flow

```python
class MyViewModel(BaseViewModel):
    def user_action(self, data):
        """User performs action in UI"""
        # 1. Validate input
        if not self._validate(data):
            return

        # 2. Update local state
        self._local_state = data

        # 3. Update central state
        store = get_store()
        store.update(my_slice=new_state)

        # 4. Publish event
        bus = get_event_bus()
        bus.publish(Event(
            type=EventType.CUSTOM,
            payload=data
        ))
```

### Pattern 2: Reacting to External Changes

```python
class MyViewModel(BaseViewModel):
    def initialize(self):
        """Setup subscriptions"""
        # Subscribe to state changes
        self._store.subscribe(
            StateEvent.GRAPH_CHANGED,
            self._on_graph_changed
        )

        # Subscribe to events
        self._event_bus.subscribe(
            EventType.NODE_CREATED,
            self._on_node_created
        )

    def _on_graph_changed(self, state_slice):
        """React to graph change"""
        # Update local state from central state
        self._sync_from_state()

    def _on_node_created(self, event):
        """React to node creation event"""
        # Update UI or trigger other actions
        pass
```

### Pattern 3: Observable Properties

```python
class MyViewModel(BaseViewModel):
    # Define observable property
    zoom_level = ObservableProperty("zoom_level", default=1.0)

    def __init__(self):
        super().__init__()
        # Property is automatically observable

    def set_zoom(self, new_zoom):
        """Update zoom level"""
        # Property setter notifies observers
        self.zoom_level = new_zoom

class MyView(BaseView):
    def _bind_viewmodel(self):
        """Bind to observable properties"""
        self._viewmodel.observe_property(
            "zoom_level",
            self._on_zoom_changed
        )

    def _on_zoom_changed(self, old_value, new_value):
        """React to zoom change"""
        # Update UI
        self._update_zoom_display(new_value)
```

## Testing Best Practices

### Unit Test Guidelines

```python
# ✓ GOOD: Test pure logic
def test_calculation_correct():
    vm = CalculatorViewModel()
    result = vm.add(2, 3)
    assert result == 5

# ✓ GOOD: Test state updates
def test_state_updated():
    vm = MyViewModel()
    vm.update_something()
    state = get_store().get_state()
    assert state.my_slice.property == expected_value

# ✗ BAD: Don't test PyQt in unit tests
def test_button_click():  # This belongs in integration test
    view = MyView(vm)
    view.button.click()  # Requires QApplication
```

### Integration Test Guidelines

```python
# ✓ GOOD: Test view-viewmodel interaction
@pytest.fixture
def qapp():
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    return QApplication.instance() or QApplication([])

def test_view_updates_from_viewmodel(qapp):
    vm = MyViewModel()
    view = MyView(vm)

    vm.update_value(42)

    assert view.label.text() == "42"

# ✓ GOOD: Test user interaction
def test_button_updates_viewmodel(qapp):
    vm = MyViewModel()
    view = MyView(vm)

    view.button.click()

    assert vm.some_property == expected_value
```

### Mocking Guidelines

```python
from unittest.mock import Mock, patch

def test_with_mock_store():
    """Test with mocked state store"""
    mock_store = Mock()
    mock_store.get_state.return_value = Mock(
        execution=Mock(is_running=True)
    )

    with patch('gui_framework.viewmodels.my_vm.get_store', return_value=mock_store):
        vm = MyViewModel()
        vm.some_action()

        # Verify store was updated
        mock_store.update.assert_called_once()
```

## Debugging Tips

### Enable Debug Logging

```python
# In your viewmodel
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class MyViewModel(BaseViewModel):
    def user_action(self):
        logger.debug("User action triggered")
        # ...
```

### Time-Travel Debugging

```python
# State store has built-in history
store = get_store()

# Go back one state
store.undo()

# Go forward one state
store.redo()

# Inspect history
print(f"History size: {len(store._history)}")
print(f"Current index: {store._history_index}")
```

### Profile Performance

```python
from gui_framework.profiling.profiler import profile_method

class MyViewModel(BaseViewModel):
    @profile_method
    def expensive_operation(self):
        """This will print profiling stats"""
        # ... expensive code ...
```

## Common Issues and Solutions

### Issue: "Cannot import gui_framework"

**Solution**: Install package in editable mode
```bash
pip install -e .
```

### Issue: "libEGL.so.1: cannot open shared object file"

**Solution**: For headless testing
```bash
export QT_QPA_PLATFORM=offscreen
```

Or install system libraries:
```bash
sudo apt-get install libegl1 libgl1 libdbus-1-3
```

### Issue: Tests hang with GUI

**Solution**: Use pytest-qt plugin
```bash
pip install pytest-qt
```

And use `qtbot` fixture:
```python
def test_my_widget(qtbot):
    widget = MyWidget()
    qtbot.addWidget(widget)
    # Test will auto-cleanup
```

### Issue: State not updating

**Solution**: Check immutability
```python
# ✗ BAD: Mutating state
state.execution.is_running = True  # Won't work!

# ✓ GOOD: Creating new state
new_execution = ExecutionState(
    **{**state.execution.__dict__, "is_running": True}
)
store.update(execution=new_execution)
```

## Contributing Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Keep functions small (<50 lines)
- Prefer composition over inheritance

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b gui/rebuild/feature-name

# 2. Make changes
# ... edit files ...

# 3. Write tests
# ... add tests ...

# 4. Run tests
pytest gui_tests/

# 5. Commit (use conventional commits)
git add .
git commit -m "feat: add counter widget"

# 6. Push and create PR
git push origin gui/rebuild/feature-name
```

### PR Checklist

- [ ] Code follows style guide
- [ ] Tests added (unit + integration)
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Changelog updated (if user-facing)
- [ ] Feature flag added (if experimental)
- [ ] Backward compatibility maintained

## Resources

### Documentation
- [Feature Inventory](FEATURE_INVENTORY.md)
- [Target Architecture](TARGET_ARCHITECTURE.md)
- [Migration Plan](MIGRATION_PLAN.md)
- [GUI README](../../GUI_README.md)

### External Resources
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [MVVM Pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93viewmodel)
- [pytest Documentation](https://docs.pytest.org/)

### Getting Help

- Open an issue on GitHub
- Ask in team chat
- Review existing widgets for examples
- Check test files for usage patterns

## Quick Reference

### Imports

```python
# State management
from gui_framework.state.store import get_store, StateEvent
from gui_framework.state.models import AppState, ExecutionState, CanvasState

# Events
from gui_framework.events.bus import get_event_bus, Event, EventType

# Base classes
from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty
from gui_framework.views.base import BaseView

# Registry
from gui_framework.registry.widget_registry import get_widget_registry

# Window manager
from gui_framework.window.manager import get_window_manager
```

### Common Commands

```bash
# Run GUI
python run_gui.py

# Run all tests
pytest

# Run specific tests
pytest gui_tests/unit/ -v
pytest gui_tests/integration/ -v -s

# Run with coverage
pytest --cov=gui_framework --cov-report=html

# Format code
black gui_framework/
isort gui_framework/

# Type check
mypy gui_framework/

# Lint
ruff gui_framework/
```

## Summary

You now know:
- ✅ How to set up the development environment
- ✅ How to create ViewModels (pure Python, testable)
- ✅ How to create Views (PyQt6 UI)
- ✅ How to use State Store and Event Bus
- ✅ How to write unit and integration tests
- ✅ Common patterns and best practices
- ✅ How to debug and troubleshoot

**Next Steps**:
1. Try creating the counter widget example
2. Review existing widgets for patterns
3. Write tests before views (TDD)
4. Ask questions when stuck!

Happy coding! 🚀
