# GUI Rebuild Testing Instructions

## Quick Start - Test the New MVVM Framework

This guide provides comprehensive instructions for testing the new GUI framework that has been built so far.

## Current Status (Phase 3 - PR #7 Complete)

**✅ Complete:**
- Phase 0: Documentation (6 comprehensive documents)
- Phase 1: Core framework (State Store, Event Bus, Base Classes)
- Phase 2: Proof of concept (CollapsibleSection widget)
- Phase 3: ExecutionViewModel + ExecutionView (full execution controls)

**📊 Metrics:**
- 167 tests passing (100%)
- ~4,800 LOC of framework code
- ~2,600 LOC of test code
- ~18% of GUI migrated
- Execution time: <0.2 seconds

## Testing Methods

### 1. Interactive Demo Application (Recommended)

The demo application showcases all implemented components with a working UI.

#### Prerequisites
```bash
pip install PyQt6
```

#### Run Demo
```bash
cd /path/to/ComputationalGraphs
python demo_new_gui.py
```

#### What You'll See

**Main Window:**
- Title: "MVVM GUI Framework Demo"
- Three main sections with working controls

**Counter Widget** (Top section):
- Large number display (starts at 0)
- Three buttons: `-` (decrement), `Reset`, `+` (increment)
- Step size spinner (default: 1, range: 1-100)
- Info label showing last action

**Execution Controls** (Middle section):
- Status display (IDLE/RUNNING/PAUSED/COMPLETED)
- Iteration counter (Current: X / Max: Y)
- Six control buttons:
  - ▶ Play: Start execution
  - ⏸ Pause: Pause execution
  - ⏵ Resume: Continue from pause
  - ⏭ Step: Execute single step
  - ⏮ Reset: Return to initial state
  - ⏹ Stop: Stop immediately
- Speed slider (0-1000ms)
- Max Speed checkbox
- Max Steps spinner (1-1,000,000)

**CollapsibleSection** (Bottom section):
- Header: "Advanced Options" with arrow icon
- Click to expand/collapse
- Arrow changes direction (down/right)
- Content area shows/hides

**Console Output:**
- Real-time logging of ViewModel/View interactions
- Event bus activity
- State changes

#### Testing Procedures

**Test 1: Counter Widget**
1. Click `+` button → Counter increases by 1
2. Click `-` button → Counter decreases by 1
3. Change step size to 5
4. Click `+` → Counter increases by 5
5. Click `Reset` → Counter returns to 0
6. Verify console shows: "[ViewModel] Incremented to X"
7. Verify console shows: "[View] Count display updated: Y -> X"

**Test 2: Observable Properties**
1. Change counter value
2. Watch UI update automatically (no manual refresh)
3. Verify info label updates with last action
4. Console shows observer notifications

**Test 3: Event Bus**
1. Perform any counter action
2. Console shows: "[View] Event received: <Event>"
3. Verify events published for each action
4. Multiple observers receive same event

**Test 4: Execution Controls - Basic**
1. Click Play → Status changes to RUNNING
2. Iteration counter starts incrementing
3. Play button becomes disabled
4. Pause button becomes enabled
5. Click Pause → Status changes to PAUSED
6. Counter stops incrementing
7. Resume button becomes enabled

**Test 5: Execution Controls - Advanced**
1. Set max steps to 100
2. Click Play → Execution runs to 100 then stops
3. Status shows COMPLETED
4. Resume button remains enabled (can extend)
5. Click Resume → Execution continues beyond 100
6. Click Stop → Execution stops immediately
7. Status returns to IDLE

**Test 6: Speed Control**
1. Move slider to 500ms → Speed updates in real-time
2. Execution slows down (if running)
3. Check "Max Speed" → Slider disables
4. Speed display shows "Max Speed"
5. Execution runs as fast as possible
6. Uncheck → Slider re-enables, speed restores

**Test 7: Step-by-Step Execution**
1. Ensure status is IDLE or PAUSED
2. Click Step → Single iteration executes
3. Counter increases by 1
4. Status remains IDLE/PAUSED
5. Click Step again → Another iteration
6. Repeat to verify consistent behavior

**Test 8: Reset Functionality**
1. Run execution to any point
2. Click Reset → Iteration counter returns to 0
3. Status returns to IDLE
4. All buttons return to initial state
5. Max steps and speed preserved

**Test 9: CollapsibleSection**
1. Click "Advanced Options" header
2. Content area expands smoothly
3. Arrow changes from right (▸) to down (▾)
4. Click again → Content collapses
5. Arrow returns to right
6. State persists (remembers expanded/collapsed)

**Test 10: Theme Integration**
1. All widgets use consistent styling
2. Colors match existing theme
3. Buttons have hover effects
4. Focus indicators visible
5. No visual glitches or misalignments

#### Expected Console Output

```
Initializing MVVM GUI Framework...
State Store initialized
Event Bus initialized
Window Manager initialized

=== Testing Counter Widget ===
[ViewModel] Initialized with count=0
[View] Counter view initialized
[ViewModel] Incremented to 1
[View] Count display updated: 0 -> 1
[View] Event received: <Event type=EventType.COUNTER_CHANGED>

=== Testing Execution Controls ===
[ExecutionViewModel] Initialized: max_steps=1000, speed=100ms
[ExecutionView] View initialized
[ExecutionViewModel] Play called: IDLE -> RUNNING
[View] Status changed: IDLE -> RUNNING
[View] Button states updated
[ExecutionViewModel] Pause called: RUNNING -> PAUSED
...
```

### 2. Unit Tests (Fast, No GUI Required)

Unit tests validate framework logic without PyQt dependencies.

#### Run All Tests
```bash
cd /path/to/ComputationalGraphs
python -m pytest gui_tests/unit/ -v
```

#### Expected Output
```
============================== test session starts ===============================
collected 167 items

gui_tests/unit/test_state_store.py::TestStateStore::test_store_initialization PASSED
gui_tests/unit/test_state_store.py::TestStateStore::test_state_immutability PASSED
...
gui_tests/unit/test_execution_view.py::TestExecutionView::test_view_initialization PASSED
gui_tests/unit/test_execution_view.py::TestExecutionView::test_button_states PASSED

=============================== 167 passed in 0.18s ==============================
```

#### Test by Component

**State Management:**
```bash
python -m pytest gui_tests/unit/test_state_store.py -v  # 24 tests
python -m pytest gui_tests/unit/test_state_models.py -v  # 16 tests
```

**Event Bus:**
```bash
python -m pytest gui_tests/unit/test_event_bus.py -v  # 24 tests
```

**Base Classes:**
```bash
python -m pytest gui_tests/unit/viewmodels/test_base_viewmodel.py -v  # 13 tests
python -m pytest gui_tests/unit/test_widget_registry.py -v  # 13 tests
python -m pytest gui_tests/unit/test_window_manager.py -v  # 13 tests
```

**Widgets:**
```bash
python -m pytest gui_tests/unit/test_collapsible_section_viewmodel.py -v  # 16 tests
python -m pytest gui_tests/unit/test_execution_viewmodel.py -v  # 25 tests
python -m pytest gui_tests/unit/test_execution_view.py -v  # 23 tests
```

#### Test Coverage Report
```bash
python -m pytest gui_tests/unit/ --cov=gui_framework --cov-report=html
# Open htmlcov/index.html to see coverage report
```

**Expected Coverage:**
- State Store: >95%
- Event Bus: >95%
- ViewModels: >90%
- Views: >85%
- Overall: >85%

### 3. Manual Code Inspection

#### Framework Structure
```
gui_framework/
├── __init__.py                         # Package initialization
├── state/
│   ├── __init__.py                     # State exports
│   ├── models.py                       # Immutable state dataclasses
│   └── store.py                        # StateStore with history
├── events/
│   ├── __init__.py                     # Event exports
│   └── bus.py                          # EventBus pub/sub
├── viewmodels/
│   ├── __init__.py                     # ViewModel exports
│   ├── base.py                         # BaseViewModel + ObservableProperty
│   ├── execution_viewmodel.py         # Execution control logic
│   └── collapsible_section_viewmodel.py
├── views/
│   ├── __init__.py                     # View exports
│   ├── base.py                         # BaseView
│   ├── execution_view.py               # Execution UI
│   └── collapsible_section_view.py
├── registry/
│   ├── __init__.py                     # Registry exports
│   └── widget_registry.py             # Plugin system
├── window/
│   ├── __init__.py                     # Window exports
│   └── manager.py                      # WindowManager
└── widgets/
    └── (CollapsibleSection components)
```

#### Verify Pattern Implementation

**Check ViewModel (Pure Python):**
```python
# gui_framework/viewmodels/execution_viewmodel.py
class ExecutionViewModel(BaseViewModel):
    # ✅ Uses ObservableProperty
    status = ObservableProperty("status", default=ExecutionStatus.IDLE)

    # ✅ Business logic only
    def play(self):
        self.status = ExecutionStatus.RUNNING
        self._event_bus.publish(Event(EventType.EXECUTION_STARTED))

    # ✅ No PyQt imports
    # ✅ No UI code
```

**Check View (Thin UI):**
```python
# gui_framework/views/execution_view.py
class ExecutionView(BaseView):
    # ✅ Inherits from BaseView

    def _setup_ui(self):
        # ✅ Creates PyQt widgets only
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self._viewmodel.play)

    def _bind_viewmodel(self):
        # ✅ Observes ViewModel properties
        self._viewmodel.observe_property("status", self._on_status_changed)

    def _on_status_changed(self, old, new):
        # ✅ Updates UI based on ViewModel
        self.play_button.setEnabled(self._viewmodel.can_play)

    # ✅ No business logic
```

### 4. Integration Verification

#### Check State Store Integration
```bash
python -c "
from gui_framework.state import get_store
store = get_store()
print(f'State Store: {store}')
print(f'Initial state: {store.state}')
store.update(execution={'is_running': True})
print(f'Updated state: {store.state.execution.is_running}')
print('✅ State Store working')
"
```

#### Check Event Bus Integration
```bash
python -c "
from gui_framework.events import get_event_bus, Event, EventType

bus = get_event_bus()
events_received = []

def handler(event):
    events_received.append(event)

bus.subscribe(EventType.EXECUTION_STARTED, handler)
bus.publish(Event(type=EventType.EXECUTION_STARTED))

assert len(events_received) == 1
print('✅ Event Bus working')
"
```

#### Check ViewModel Instantiation
```bash
python -c "
from gui_framework.viewmodels import ExecutionViewModel

vm = ExecutionViewModel()
print(f'ViewModel: {vm}')
print(f'Status: {vm.status}')
vm.play()
print(f'After play: {vm.status}')
print('✅ ViewModel working')
"
```

## Troubleshooting

### Demo Won't Start

**Issue:** `ModuleNotFoundError: No module named 'PyQt6'`
```bash
pip install PyQt6
```

**Issue:** `ImportError: cannot import name 'get_store'`
```bash
# Ensure you're in the correct directory
cd /path/to/ComputationalGraphs
python demo_new_gui.py
```

**Issue:** Demo window appears but is blank
- Check console for error messages
- Verify PyQt6 version: `python -c "import PyQt6; print(PyQt6.__version__)"`
- Should be 6.4.0 or higher

### Tests Fail

**Issue:** `pytest: command not found`
```bash
pip install pytest
```

**Issue:** Some tests fail
```bash
# Run with verbose output to see which tests
python -m pytest gui_tests/unit/ -v --tb=short

# Run specific failing test
python -m pytest gui_tests/unit/test_execution_view.py::TestExecutionView::test_view_initialization -vv
```

**Issue:** Import errors in tests
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/path/to/ComputationalGraphs:$PYTHONPATH
python -m pytest gui_tests/unit/ -v
```

### Performance Issues

**Issue:** Demo is slow or unresponsive
- This shouldn't happen with current code (all fast)
- Check system resources
- Try running tests instead (no GUI overhead)

## Success Criteria

### Demo Application
- ✅ Window opens without errors
- ✅ Counter widget responsive
- ✅ Execution controls change state
- ✅ CollapsibleSection expands/collapses
- ✅ Console shows clear logs
- ✅ No exceptions in console
- ✅ Clean shutdown when closed

### Unit Tests
- ✅ All 167 tests pass
- ✅ Execution time <1 second
- ✅ No warnings or errors
- ✅ Coverage >80%

### Code Quality
- ✅ ViewModels have no PyQt imports
- ✅ Views have no business logic
- ✅ Observable properties work
- ✅ Event bus delivers events
- ✅ State Store tracks state

## Next Steps

### For Users/Testers
1. Run demo application (`python demo_new_gui.py`)
2. Test all features per testing procedures
3. Run unit tests (`python -m pytest gui_tests/unit/ -v`)
4. Report any issues or unexpected behavior

### For Developers
1. Review code structure and patterns
2. Study ViewModel/View separation
3. Understand ObservableProperty pattern
4. Learn Event Bus usage
5. Explore State Store capabilities

### For Migration Continuation
Per user request "continue the GUI Migration", next steps are:

**Phase 3 Remaining** (4-6 days):
- PR #8: Node Palette (PaletteViewModel + PaletteView)
- PR #9: Theme Manager migration
- PR #10: File I/O controls

**Phase 4** (5-8 days):
- Canvas migration (highest complexity, 2606 LOC)

**Phase 5** (8-12 days):
- Remaining features (dialogs, plots, etc.)

**Phase 6** (5-7 days):
- Polish, documentation, release

See `MIGRATION_STATUS.md` for complete tracking.

## Documentation References

- **Architecture Design**: `TARGET_ARCHITECTURE.md`
- **Migration Plan**: `MIGRATION_PLAN.md`
- **Developer Guide**: `DEVELOPER_QUICKSTART.md`
- **Testing Guide**: `TESTING_GUIDE.md`
- **Migration Status**: `MIGRATION_STATUS.md`
- **Feature Inventory**: `FEATURE_INVENTORY.md`

## Contact & Support

For questions or issues:
1. Check existing documentation in `docs/gui_rebuild/`
2. Review demo application source: `demo_new_gui.py`
3. Examine test files in `gui_tests/unit/`
4. Open issue in repository with:
   - What you were trying to do
   - Expected behavior
   - Actual behavior
   - Console output/error messages
   - Operating system and Python version

---

**Last Updated**: Phase 3 PR #7 Complete (ExecutionView)
**Test Status**: 167/167 passing (100%)
**Demo Status**: Working ✅
