# Testing Guide for New MVVM GUI Framework

## Overview

This guide explains how to test the new GUI framework components, including unit tests, integration tests, and manual UI testing.

## Quick Start

### Run All Framework Tests

```bash
# Run all unit tests (no GUI needed)
python -m pytest gui_tests/unit/ -v

# Run with coverage report
python -m pytest gui_tests/unit/ --cov=gui_framework --cov-report=html

# Run specific test file
python -m pytest gui_tests/unit/test_state_store.py -v
```

### Run Demo Application

```bash
# Install PyQt6 if not already installed
pip install PyQt6

# Run the demo
python demo_new_gui.py
```

The demo application shows:
- Counter widget with MVVM pattern
- Observable properties with automatic UI updates
- Event bus integration
- CollapsibleSection widget from new framework
- Console logging of ViewModel/View interactions

## Test Organization

```
gui_tests/
└── unit/                          # Pure Python tests (no GUI)
    ├── test_state_store.py        # State management (24 tests)
    ├── test_state_models.py       # State dataclasses (16 tests)
    ├── test_event_bus.py          # Event system (24 tests)
    ├── viewmodels/test_base_viewmodel.py     # ViewModel base class (13 tests)
    ├── test_widget_registry.py    # Plugin system (13 tests)
    ├── test_window_manager.py     # Window lifecycle (13 tests)
    ├── test_collapsible_section_viewmodel.py  # Widget (16 tests)
    └── test_execution_viewmodel.py            # Execution control (25 tests)
```

**Total: 144 tests, all passing**

## Unit Testing ViewModels

ViewModels are pure Python with no PyQt dependencies, making them fast and easy to test.

### Example: Testing a ViewModel

```python
import pytest
from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty

class MyViewModel(BaseViewModel):
    count = ObservableProperty("count", default=0)
    
    def increment(self):
        self.count += 1

def test_increment():
    """Test that increment increases count."""
    vm = MyViewModel()
    assert vm.count == 0
    
    vm.increment()
    assert vm.count == 1
    
def test_observable_property():
    """Test that observers are notified."""
    vm = MyViewModel()
    
    changes = []
    def observer(old, new):
        changes.append((old, new))
    
    vm.observe_property("count", observer)
    
    vm.count = 5
    assert changes == [(0, 5)]
    
def test_event_publishing():
    """Test that events are published."""
    vm = MyViewModel()
    
    events = []
    def listener(event):
        events.append(event)
    
    vm._event_bus.subscribe(EventType.NODE_UPDATED, listener)
    
    # Your ViewModel method that publishes events
    vm.increment()
    
    assert len(events) > 0
```

### Running ViewModel Tests

```bash
# Run all ViewModel tests
python -m pytest gui_tests/unit/test_*viewmodel.py -v

# Run with detailed output
python -m pytest gui_tests/unit/test_execution_viewmodel.py -v -s
```

## Integration Testing (Views + ViewModels)

Integration tests require PyQt6 and may need headless setup for CI.

### Headless Testing Setup

For CI or headless environments:

```bash
# Linux: Install Xvfb
sudo apt-get install xvfb

# Run tests with Xvfb
xvfb-run python -m pytest gui_tests/integration/ -v

# Or use environment variable
export QT_QPA_PLATFORM=offscreen
python -m pytest gui_tests/integration/ -v
```

### Example: Integration Test Template

```python
import pytest
from PyQt6.QtWidgets import QApplication
from gui_framework.widgets.collapsible_section_view import CollapsibleSectionView
from gui_framework.widgets.collapsible_section_viewmodel import CollapsibleSectionViewModel

@pytest.fixture
def qapp():
    """Provide QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_collapsible_section_ui(qapp):
    """Test CollapsibleSection UI integration."""
    # Create ViewModel
    vm = CollapsibleSectionViewModel(title="Test", expanded=True)
    
    # Create View
    from PyQt6.QtWidgets import QLabel
    content = QLabel("Content")
    view = CollapsibleSectionView(vm, content_widget=content)
    
    # Test initial state
    assert view.toggle_button.text() == "Test"
    assert content.isVisible()
    
    # Toggle
    vm.toggle()
    assert not content.isVisible()
```

## Manual UI Testing

### 1. Demo Application

The `demo_new_gui.py` shows all framework features:

```bash
python demo_new_gui.py
```

**What to test:**
- Click + and - buttons (should update counter display)
- Change step size (should affect increment/decrement)
- Click Reset (should go back to 0)
- Watch console for ViewModel/View logs
- Expand/collapse "Advanced Options" section

### 2. Framework Components

Test individual components:

```python
# Test State Store
python -c "
from gui_framework.state.store import get_store
from gui_framework.state.models import ExecutionState

store = get_store()
print('Initial state:', store.state)

# Update state
store.update(execution=ExecutionState(is_running=True))
print('After update:', store.state.execution.is_running)

# Undo
store.undo()
print('After undo:', store.state.execution.is_running)
"

# Test Event Bus
python -c "
from gui_framework.events.bus import get_event_bus, Event, EventType

bus = get_event_bus()

def listener(event):
    print(f'Received event: {event.type}')

bus.subscribe(EventType.NODE_CREATED, listener)
bus.publish(Event(type=EventType.NODE_CREATED, payload={}))
"
```

## Test Coverage

### Current Coverage

```bash
# Generate coverage report
python -m pytest gui_tests/unit/ --cov=gui_framework --cov-report=term

# Generate HTML report
python -m pytest gui_tests/unit/ --cov=gui_framework --cov-report=html
open htmlcov/index.html
```

**Current Status**: >90% coverage for all framework components

### Coverage Targets

- State Store: >90% ✅
- Event Bus: >90% ✅
- ViewModels: >80% ✅
- Views: >70% (harder to test, some manual testing needed)
- Registry: >85% ✅
- Window Manager: >85% ✅

## Common Testing Scenarios

### Testing Observable Properties

```python
def test_observable_triggers_ui_update():
    """Test that changing a property triggers observer."""
    vm = MyViewModel()
    
    observer_called = []
    def observer(old, new):
        observer_called.append(True)
    
    vm.observe_property("my_property", observer)
    vm.my_property = "new_value"
    
    assert len(observer_called) == 1
```

### Testing Event Publishing

```python
def test_action_publishes_event():
    """Test that ViewModel action publishes correct event."""
    vm = MyViewModel()
    
    events = []
    def listener(event):
        events.append(event)
    
    vm._event_bus.subscribe(EventType.MY_EVENT, listener)
    vm.do_action()
    
    assert len(events) == 1
    assert events[0].type == EventType.MY_EVENT
```

### Testing State Updates

```python
def test_action_updates_state():
    """Test that ViewModel updates central state."""
    vm = MyViewModel()
    store = get_store()
    
    initial_state = store.state
    vm.do_action()
    
    assert store.state != initial_state
    assert store.state.my_field == "expected_value"
```

### Testing Lifecycle

```python
def test_viewmodel_lifecycle():
    """Test initialize and cleanup are called."""
    class TestVM(BaseViewModel):
        def __init__(self):
            super().__init__()
            self.init_called = False
            self.cleanup_called = False
        
        def initialize(self):
            self.init_called = True
        
        def cleanup(self):
            self.cleanup_called = True
    
    vm = TestVM()
    
    # Simulate View lifecycle
    vm.initialize()
    assert vm.init_called
    
    vm.cleanup()
    assert vm.cleanup_called
```

## Debugging Tips

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all framework logs will be visible
vm = MyViewModel()
vm.increment()  # Will log state changes
```

### Inspect State History

```python
from gui_framework.state.store import get_store

store = get_store()

# Make some changes
store.update(execution=ExecutionState(is_running=True))
store.update(execution=ExecutionState(is_running=False))

# Check history
print(f"History length: {len(store._history)}")
print(f"Current position: {store._current_index}")

# Travel through history
store.undo()
print(f"After undo: {store.state.execution.is_running}")
```

### Monitor Events

```python
from gui_framework.events.bus import get_event_bus, EventType

bus = get_event_bus()

# Subscribe to all events (for debugging)
def debug_listener(event):
    print(f"[DEBUG] Event: {event.type}, Payload: {event.payload}")

# Subscribe to specific events
bus.subscribe(EventType.NODE_CREATED, debug_listener)
bus.subscribe(EventType.NODE_UPDATED, debug_listener)
bus.subscribe(EventType.EXECUTION_STARTED, debug_listener)
```

## Performance Testing

### Benchmark State Updates

```python
import time
from gui_framework.state.store import get_store
from gui_framework.state.models import ExecutionState

store = get_store()

start = time.time()
for i in range(1000):
    store.update(execution=ExecutionState(current_step=i))
elapsed = time.time() - start

print(f"1000 state updates in {elapsed:.3f}s ({1000/elapsed:.0f} updates/sec)")
```

### Benchmark Event Publishing

```python
import time
from gui_framework.events.bus import get_event_bus, Event, EventType

bus = get_event_bus()

def dummy_listener(event):
    pass

bus.subscribe(EventType.NODE_UPDATED, dummy_listener)

start = time.time()
for i in range(10000):
    bus.publish(Event(type=EventType.NODE_UPDATED, payload={"i": i}))
elapsed = time.time() - start

print(f"10000 events in {elapsed:.3f}s ({10000/elapsed:.0f} events/sec)")
```

## CI Configuration

### pytest.ini Configuration

```ini
[tool:pytest]
testpaths = gui_tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    unit: Pure Python unit tests (no GUI)
    integration: Integration tests (requires PyQt6)
    slow: Slow tests (performance, stress tests)
```

### GitHub Actions Example

```yaml
name: GUI Framework Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install pytest pytest-cov
        pip install PyQt6
    
    - name: Install Xvfb (for headless GUI tests)
      run: |
        sudo apt-get update
        sudo apt-get install -y xvfb
    
    - name: Run unit tests
      run: |
        python -m pytest gui_tests/unit/ -v --cov=gui_framework
    
    - name: Run integration tests (headless)
      run: |
        xvfb-run python -m pytest gui_tests/integration/ -v
      env:
        QT_QPA_PLATFORM: offscreen
```

## Troubleshooting

### PyQt6 Import Errors

```bash
# Install PyQt6
pip install PyQt6

# If still fails, try
pip install PyQt6-Qt6 PyQt6-sip
```

### Headless Testing Fails

```bash
# Set environment variable
export QT_QPA_PLATFORM=offscreen

# Or use Xvfb
xvfb-run -a python -m pytest gui_tests/integration/ -v
```

### Test Discovery Issues

```bash
# Make sure __init__.py files exist
touch gui_tests/__init__.py
touch gui_tests/unit/__init__.py
touch gui_tests/integration/__init__.py

# Run from project root
cd /path/to/ComputationalGraphs
python -m pytest gui_tests/unit/ -v
```

### Observable Property Not Triggering

```python
# Make sure you're using assignment, not mutation
vm.count = 5       # ✅ Triggers observers
vm.count += 1      # ✅ Triggers observers
vm.list.append(x)  # ❌ Does NOT trigger (mutation)

# For mutable objects, reassign:
new_list = vm.list.copy()
new_list.append(x)
vm.list = new_list  # ✅ Triggers observers
```

## Test Data and Fixtures

### Pytest Fixtures

```python
import pytest
from gui_framework.state.store import StateStore
from gui_framework.events.bus import EventBus

@pytest.fixture
def clean_store():
    """Provide fresh StateStore for each test."""
    store = StateStore()
    store.reset()
    return store

@pytest.fixture
def clean_bus():
    """Provide fresh EventBus for each test."""
    bus = EventBus()
    # Clear all subscriptions
    for event_type in EventType:
        if event_type in bus._subscribers:
            bus._subscribers[event_type].clear()
    return bus

@pytest.fixture
def sample_viewmodel():
    """Provide a sample ViewModel for testing."""
    class SampleVM(BaseViewModel):
        value = ObservableProperty("value", default=0)
    return SampleVM()
```

## Next Steps

1. **Run demo application** to see framework in action
2. **Run unit tests** to verify framework works correctly
3. **Write tests for your widgets** following the patterns shown
4. **Set up CI** with headless PyQt testing
5. **Measure coverage** to ensure >80% for new code

## Questions?

Check the documentation:
- Architecture: `docs/gui_rebuild/TARGET_ARCHITECTURE.md`
- Developer Guide: `docs/gui_rebuild/DEVELOPER_QUICKSTART.md`
- Migration Plan: `docs/gui_rebuild/MIGRATION_PLAN.md`
