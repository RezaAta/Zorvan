# Testing Guidelines for GUI Rebuild & Migration

## Overview

This document provides comprehensive testing guidelines for the GUI rebuild project, covering unit tests, integration tests, and manual testing procedures.

## Test Infrastructure

### Test Organization

```
gui_tests/
├── unit/                       # Pure Python unit tests (no GUI)
│   ├── test_state_store.py
│   ├── test_event_bus.py
│   ├── test_execution_viewmodel.py
│   ├── test_theme_viewmodel.py
│   ├── test_theme_mixin.py
│   └── ...
└── integration/                # Integration tests (headless PyQt)
    └── (to be added)
```

### Running Tests

#### All Tests
```bash
# Run all GUI tests
python -m pytest gui_tests/unit/ -v

# Run with coverage
python -m pytest gui_tests/unit/ --cov=gui_framework --cov-report=html

# Quick run (quiet mode)
python -m pytest gui_tests/unit/ -q
```

#### Specific Test Files
```bash
# Run tests for a specific component
python -m pytest gui_tests/unit/test_theme_viewmodel.py -v

# Run a specific test class
python -m pytest gui_tests/unit/test_theme_viewmodel.py::TestThemeViewModel -v

# Run a single test
python -m pytest gui_tests/unit/test_theme_viewmodel.py::TestThemeViewModel::test_initialization -xvs
```

#### Test Options
- `-v`: Verbose output
- `-q`: Quiet mode (summary only)
- `-x`: Stop on first failure
- `-s`: Show print statements
- `--tb=short`: Shorter traceback format
- `--maxfail=3`: Stop after 3 failures

## Unit Testing Guidelines

### ViewModels (Pure Python Tests)

ViewModels should be tested without any PyQt dependencies. These tests are fast and reliable.

**Example Structure:**
```python
class TestMyViewModel:
    """Test suite for MyViewModel."""
    
    def test_initialization(self):
        """Test ViewModel initializes with correct defaults."""
        vm = MyViewModel()
        vm.initialize()
        
        assert vm.some_property == expected_value
        
        vm.cleanup()
    
    def test_observable_property(self):
        """Test that property changes trigger observers."""
        vm = MyViewModel()
        vm.initialize()
        
        # Observe property
        callback_called = []
        
        def callback(old_value, new_value):
            callback_called.append((old_value, new_value))
        
        vm.observe_property("my_property", callback)
        
        # Change property
        vm.my_property = "new_value"
        
        # Verify callback was called
        assert len(callback_called) == 1
        assert callback_called[0][1] == "new_value"
        
        vm.cleanup()
    
    def test_event_publishing(self):
        """Test that actions publish events."""
        vm = MyViewModel()
        vm.initialize()
        
        # Subscribe to events
        events = []
        
        def handler(event):
            events.append(event)
        
        vm._event_bus.subscribe(EventType.MY_EVENT, handler)
        
        # Perform action
        vm.do_something()
        
        # Verify event was published
        assert len(events) == 1
        assert events[0].type == EventType.MY_EVENT
        
        vm.cleanup()
```

**Best Practices:**
1. Always call `initialize()` after creating ViewModel
2. Always call `cleanup()` after test completes
3. Test observable properties by subscribing callbacks
4. Test event publishing by subscribing to event bus
5. Test state store integration by checking state updates
6. Keep tests independent (don't rely on test execution order)

### State Store Testing

**Test Patterns:**
```python
def test_state_update():
    """Test state updates work correctly."""
    vm = MyViewModel()
    vm.initialize()
    
    # Perform action that updates state
    vm.set_something("value")
    
    # Verify state was updated
    state = vm._store.get_state()
    assert state.my_slice.my_field == "value"
    
    vm.cleanup()
```

**Important**: Reset state between tests if needed:
```python
from gui_framework.state.models import ThemeState

def test_with_clean_state():
    vm = ThemeViewModel()
    # Reset to defaults
    vm._store.update(theme=ThemeState())
    vm.initialize()
    
    # Now test with clean state
    assert vm.get_color("bg") == "#2b2b2b"
```

### Theme System Testing

**Testing ThemeViewModel:**
```python
def test_color_management():
    """Test color get/set operations."""
    vm = ThemeViewModel()
    vm._store.update(theme=ThemeState())  # Clean state
    vm.initialize()
    
    # Test get
    color = vm.get_color("bg")
    assert color == "#2b2b2b"
    
    # Test set
    vm.set_color("bg", "#123456")
    assert vm.get_color("bg") == "#123456"
    
    # Verify state updated
    state = vm._store.get_state()
    assert state.theme.colors["bg"] == "#123456"
    
    vm.cleanup()
```

**Testing ThemeMixin:**
```python
class MockWidget(ThemeMixin):
    def __init__(self, use_state_store=False):
        self.apply_theme_called = 0
        ThemeMixin.__init__(self, use_state_store=use_state_store)
    
    def apply_theme(self):
        self.apply_theme_called += 1

def test_theme_mixin_state_store_mode():
    """Test ThemeMixin in StateStore mode."""
    widget = MockWidget(use_state_store=True)
    
    # Check initialization
    assert widget.theme_viewmodel is not None
    assert widget.apply_theme_called >= 1
    
    # Test theme change triggers apply_theme
    initial_calls = widget.apply_theme_called
    widget.theme_viewmodel.set_color("accent", "#ff0000")
    assert widget.apply_theme_called > initial_calls
```

## Integration Testing (Future)

Integration tests will use headless PyQt to test View-ViewModel binding.

**Setup for headless testing:**
```bash
# Set environment variable
export QT_QPA_PLATFORM=offscreen

# Or in code
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
```

**Example integration test (future):**
```python
def test_execution_view_binding():
    """Test ExecutionView binds correctly to ExecutionViewModel."""
    vm = ExecutionViewModel()
    view = ExecutionView(vm)
    
    # Change ViewModel property
    vm.current_step = 50
    
    # Verify View updated
    assert view.step_label.text() == "50"
```

## Manual Testing

### Testing ThemeViewModel

```python
# In Python REPL or test script
from gui_framework.viewmodels.theme_viewmodel import ThemeViewModel

vm = ThemeViewModel()
vm.initialize()

# Test color operations
print(vm.get_color("bg"))  # Should print #2b2b2b
vm.set_color("accent", "#ff00ff")
print(vm.get_color("accent"))  # Should print #ff00ff

# Test font operations
font = vm.get_font("ui")
print(font)  # Should print {'family': 'Oswald', 'size': '12', 'weight': 'Medium'}

# Test theme reset
vm.reset_to_defaults()
print(vm.get_color("accent"))  # Should print #4a86e8 (default)

vm.cleanup()
```

### Testing ThemeMixin

```python
# Test with legacy mode
from gui_framework.widgets.theme_mixin import ThemeMixin

class TestWidget(ThemeMixin):
    def __init__(self):
        ThemeMixin.__init__(self, use_state_store=False)
    
    def apply_theme(self):
        print(f"Theme applied! Manager: {self.theme_manager is not None}")

widget = TestWidget()
# Should print: Theme applied! Manager: True

# Test with StateStore mode
class TestWidget2(ThemeMixin):
    def __init__(self):
        ThemeMixin.__init__(self, use_state_store=True)
    
    def apply_theme(self):
        if self.theme_viewmodel:
            color = self.theme_viewmodel.get_color("bg")
            print(f"Theme applied! BG color: {color}")

widget2 = TestWidget2()
# Should print: Theme applied! BG color: #2b2b2b
```

## Test Coverage

### Current Coverage
- **State Store**: 40 tests, >90% coverage
- **Event Bus**: 24 tests, >90% coverage
- **Base ViewModels**: 13 tests, >85% coverage
- **ExecutionViewModel**: 48 tests, >90% coverage
- **ThemeViewModel**: 19 tests, >90% coverage
- **ThemeMixin**: 15 tests, >85% coverage

**Total**: 198 tests, ~90% overall coverage

### Coverage Goals
- Unit tests: >80% coverage (required)
- Integration tests: >60% coverage (target)
- Critical paths: 100% coverage (required)

### Generating Coverage Reports
```bash
# Generate HTML coverage report
python -m pytest gui_tests/unit/ --cov=gui_framework --cov-report=html

# View report
# Open htmlcov/index.html in browser

# Generate terminal report
python -m pytest gui_tests/unit/ --cov=gui_framework --cov-report=term-missing
```

## Common Testing Patterns

### Testing Observable Properties
```python
def test_observable_property():
    vm = MyViewModel()
    
    observations = []
    vm.observe_property("my_prop", lambda old, new: observations.append(new))
    
    vm.my_prop = "value"
    
    assert observations == ["value"]
```

### Testing Event Publishing
```python
def test_event_publishing():
    vm = MyViewModel()
    
    events = []
    vm._event_bus.subscribe(EventType.MY_EVENT, lambda e: events.append(e))
    
    vm.trigger_action()
    
    assert len(events) == 1
    assert events[0].type == EventType.MY_EVENT
```

### Testing State Updates
```python
def test_state_update():
    vm = MyViewModel()
    
    vm.update_something("value")
    
    state = vm._store.get_state()
    assert state.my_slice.field == "value"
```

### Mocking PyQt in Tests
```python
import sys
from unittest.mock import MagicMock

# Mock PyQt6 before importing
if 'PyQt6' not in sys.modules:
    sys.modules['PyQt6'] = MagicMock()
    sys.modules['PyQt6.QtCore'] = MagicMock()
    sys.modules['PyQt6.QtWidgets'] = MagicMock()
```

## Continuous Integration

### Pre-commit Checks
```bash
# Run tests before committing
python -m pytest gui_tests/unit/ -q

# Run with coverage check
python -m pytest gui_tests/unit/ --cov=gui_framework --cov-fail-under=80
```

### CI Pipeline (Future)
```yaml
# .github/workflows/tests.yml
- name: Run tests
  run: |
    export QT_QPA_PLATFORM=offscreen
    python -m pytest gui_tests/unit/ -v --cov=gui_framework
```

## Debugging Failed Tests

### Verbose Output
```bash
# Show detailed output
python -m pytest gui_tests/unit/test_my_test.py -xvs

# Show local variables on failure
python -m pytest gui_tests/unit/test_my_test.py -l
```

### Debugging Specific Test
```python
# Add breakpoint in test
def test_something():
    vm = MyViewModel()
    import pdb; pdb.set_trace()  # Breakpoint here
    vm.do_something()
```

### Common Issues

**Issue: State persistence across tests**
```python
# Solution: Reset state before test
vm._store.update(theme=ThemeState())
```

**Issue: PyQt import errors**
```python
# Solution: Mock PyQt6 before importing
import sys
from unittest.mock import MagicMock
sys.modules['PyQt6'] = MagicMock()
```

**Issue: Event bus not triggering**
```python
# Solution: Ensure initialization
vm.initialize()  # This subscribes to events
```

## Performance Testing

### Measuring Test Speed
```bash
# Show slowest tests
python -m pytest gui_tests/unit/ --durations=10

# Fail if tests take too long
python -m pytest gui_tests/unit/ --timeout=1
```

### Expected Performance
- Unit test: <0.1s per test
- Full unit suite: <1s
- Integration test: <0.5s per test

## Best Practices Summary

### DO
✅ Test ViewModels without PyQt dependencies
✅ Use observable property patterns
✅ Test event publishing
✅ Test state store integration
✅ Clean up after tests (call `cleanup()`)
✅ Reset state when needed for isolation
✅ Use descriptive test names
✅ Test both success and error cases
✅ Aim for >80% coverage

### DON'T
❌ Don't rely on test execution order
❌ Don't use real PyQt in unit tests
❌ Don't skip cleanup in tests
❌ Don't test implementation details
❌ Don't ignore flaky tests
❌ Don't commit failing tests

## Resources

### Documentation
- `docs/gui_rebuild/TESTING_GUIDE.md` - This file
- `docs/gui_rebuild/DEVELOPER_QUICKSTART.md` - Developer guide
- `docs/gui_rebuild/TARGET_ARCHITECTURE.md` - Architecture details

### Examples
- `gui_tests/unit/test_execution_viewmodel.py` - ViewModel testing
- `gui_tests/unit/test_theme_viewmodel.py` - Theme system testing
- `gui_tests/unit/test_theme_mixin.py` - Mixin testing
- `demo_new_gui.py` - Interactive demo application

### Tools
- pytest: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- PyQt6: https://www.riverbankcomputing.com/static/Docs/PyQt6/

## Questions?

If you have questions about testing:
1. Check this guide first
2. Look at existing test examples
3. Review the architecture documentation
4. Open an issue for clarification
