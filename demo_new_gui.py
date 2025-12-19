#!/usr/bin/env python3
"""
Demo Application for New MVVM GUI Framework

This demonstrates how to use the new gui_framework with a simple
counter application that shows:
- ViewModel (pure Python logic)
- View (PyQt6 UI)
- Observable properties
- Event bus integration
- State store integration

Run with: python demo_new_gui.py
"""

import sys
from pathlib import Path

# Add gui_framework to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtWidgets import (
        QApplication,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

    HAS_PYQT = True
except ImportError:
    print("PyQt6 not installed. Install with: pip install PyQt6")
    print("This demo requires PyQt6 to show the UI.")
    HAS_PYQT = False
    sys.exit(1)

from gui_framework.events.bus import Event, EventType, get_event_bus
from gui_framework.state.store import get_store
from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty
from gui_framework.viewmodels.execution_viewmodel import (
    ExecutionStatus,
    ExecutionViewModel,
)
from gui_framework.views.base import BaseView
from gui_framework.views.execution_view import ExecutionView
from gui_framework.widgets.collapsible_section_view import CollapsibleSectionView
from gui_framework.widgets.collapsible_section_viewmodel import (
    CollapsibleSectionViewModel,
)


class CounterViewModel(BaseViewModel):
    """
    Pure Python ViewModel for a counter.

    No PyQt dependencies - fully testable without GUI.
    """

    # Observable properties - UI auto-updates when these change
    count = ObservableProperty("count", default=0)
    step_size = ObservableProperty("step_size", default=1)

    def initialize(self):
        """Called when View is shown."""
        print("[ViewModel] Counter initialized")

    def cleanup(self):
        """Called when View is closed."""
        print("[ViewModel] Counter cleanup")

    def increment(self):
        """Increment counter by step_size."""
        self.count += self.step_size
        print(f"[ViewModel] Incremented to {self.count}")

        # Publish event to event bus
        self._event_bus.publish(
            Event(
                type=EventType.NODE_UPDATED,  # Reusing existing event type
                payload={"counter": self.count},
            )
        )

    def decrement(self):
        """Decrement counter by step_size."""
        self.count -= self.step_size
        print(f"[ViewModel] Decremented to {self.count}")

    def reset(self):
        """Reset counter to zero."""
        self.count = 0
        print("[ViewModel] Reset to 0")

    def set_step_size(self, size: int):
        """Set the step size for increment/decrement."""
        self.step_size = size
        print(f"[ViewModel] Step size set to {size}")


class CounterView(BaseView):
    """
    PyQt6 View for the counter.

    Thin UI layer - all logic is in ViewModel.
    """

    def __init__(self, viewmodel: CounterViewModel, parent=None):
        """Initialize the counter view."""
        super().__init__(viewmodel, parent)
        # Get event bus singleton for event subscription
        self._event_bus = get_event_bus()
        self._setup_ui()

    def _setup_ui(self):
        """Create the UI components."""
        layout = QVBoxLayout()

        # Counter display
        self.count_label = QLabel("0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.count_label.font()
        font.setPointSize(48)
        self.count_label.setFont(font)
        layout.addWidget(self.count_label)

        # Control buttons
        button_layout = QHBoxLayout()

        self.dec_button = QPushButton("-")
        self.dec_button.clicked.connect(self._viewmodel.decrement)
        button_layout.addWidget(self.dec_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self._viewmodel.reset)
        button_layout.addWidget(self.reset_button)

        self.inc_button = QPushButton("+")
        self.inc_button.clicked.connect(self._viewmodel.increment)
        button_layout.addWidget(self.inc_button)

        layout.addLayout(button_layout)

        # Step size control
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Step Size:"))

        self.step_spinbox = QSpinBox()
        self.step_spinbox.setMinimum(1)
        self.step_spinbox.setMaximum(100)
        self.step_spinbox.setValue(1)
        self.step_spinbox.valueChanged.connect(self._viewmodel.set_step_size)
        step_layout.addWidget(self.step_spinbox)
        step_layout.addStretch()

        layout.addLayout(step_layout)

        # Info label
        self.info_label = QLabel("Click + or - to change counter")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def _bind_viewmodel(self):
        """Bind ViewModel properties to UI updates."""
        # Observe count property - update UI when it changes
        self._viewmodel.observe_property("count", self._on_count_changed)

        # Observe step_size property
        self._viewmodel.observe_property("step_size", self._on_step_size_changed)

        # Subscribe to events from event bus
        self._event_bus.subscribe(EventType.NODE_UPDATED, self._on_node_updated)

    def _on_count_changed(self, old_value, new_value):
        """Called when count property changes in ViewModel."""
        self.count_label.setText(str(new_value))
        print(f"[View] Count display updated: {old_value} -> {new_value}")

    def _on_step_size_changed(self, old_value, new_value):
        """Called when step_size property changes in ViewModel."""
        if self.step_spinbox.value() != new_value:
            self.step_spinbox.setValue(new_value)
        print(f"[View] Step size updated: {old_value} -> {new_value}")

    def _on_node_updated(self, event: Event):
        """Called when NODE_UPDATED event is published."""
        counter = event.payload.get("counter")
        if counter is not None:
            self.info_label.setText(f"Event received! Counter is now {counter}")
            print(f"[View] Event received: {event}")


class DemoMainWindow(QMainWindow):
    """Main window demonstrating the new framework."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("New MVVM GUI Framework Demo")
        self.setMinimumSize(500, 400)

        # Create central widget
        central = QWidget()
        main_layout = QVBoxLayout()

        # Title
        title = QLabel("MVVM GUI Framework Demo")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Counter widget
        counter_group = QGroupBox("Counter Example")
        counter_layout = QVBoxLayout()

        # Create ViewModel and View
        self.counter_vm = CounterViewModel()
        self.counter_view = CounterView(self.counter_vm)
        counter_layout.addWidget(self.counter_view)

        counter_group.setLayout(counter_layout)
        main_layout.addWidget(counter_group)

        # CollapsibleSection example
        collapsible_group = QGroupBox("CollapsibleSection Example")
        collapsible_layout = QVBoxLayout()

        # Create content for collapsible section
        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.addWidget(QLabel("This is collapsible content!"))
        content_layout.addWidget(QLabel("Click the section title to toggle."))
        info_btn = QPushButton("Info Button")
        info_btn.clicked.connect(
            lambda: print("[CollapsibleSection] Info button clicked")
        )
        content_layout.addWidget(info_btn)
        content.setLayout(content_layout)

        # Create CollapsibleSection with ViewModel
        self.collapsible_vm = CollapsibleSectionViewModel(
            title="Advanced Options", expanded=False
        )
        self.collapsible_view = CollapsibleSectionView(
            self.collapsible_vm, content_widget=content
        )

        collapsible_layout.addWidget(self.collapsible_view)
        collapsible_group.setLayout(collapsible_layout)
        main_layout.addWidget(collapsible_group)

        # Execution Controls example
        execution_group = QGroupBox("Execution Controls Example")
        execution_layout = QVBoxLayout()

        # Create ExecutionViewModel and ExecutionView
        self.execution_vm = ExecutionViewModel(max_steps=100, speed_ms=100)
        self.execution_view = ExecutionView(self.execution_vm)
        execution_layout.addWidget(self.execution_view)

        execution_group.setLayout(execution_layout)
        main_layout.addWidget(execution_group)

        # Create execution timer to simulate execution loop
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self._simulate_execution_step)

        # Inspector & Examples demo helpers
        from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel
        from gui_framework.viewmodels.examples_loader_viewmodel import (
            ExamplesLoaderViewModel,
        )
        from gui_framework.viewmodels.inspector_viewmodel import InspectorViewModel
        from gui_framework.viewmodels.mlp_generator_viewmodel import (
            MLPGeneratorViewModel,
        )
        from gui_framework.views.examples_loader_view import ExamplesLoaderView
        from gui_framework.views.inspector_view import InspectorView

        self.examples_vm = ExamplesLoaderViewModel()
        self.examples_view = ExamplesLoaderView(self.examples_vm)

        # Create a small generated graph and Inspector bound to a CanvasViewModel
        self.mlp_gen = MLPGeneratorViewModel()
        demo_graph = self.mlp_gen.generate(2, [3], 1)
        self._demo_canvas_vm = CanvasViewModel(demo_graph)
        self._demo_canvas_vm.initialize()

        self.inspector_vm = InspectorViewModel(self._demo_canvas_vm)
        self.inspector_vm.initialize()
        self.inspector_view = InspectorView(self.inspector_vm)

        # Select the first node so Inspector shows something
        if demo_graph.nodes:
            self._demo_canvas_vm.select_node(demo_graph.nodes[0].name)
            self._demo_canvas_vm.nodes_changed += 1

        # Subscribe to execution events to start/stop timer
        event_bus = get_event_bus()
        event_bus.subscribe(EventType.EXECUTION_STARTED, self._on_execution_started)
        event_bus.subscribe(EventType.EXECUTION_PAUSED, self._on_execution_paused)
        event_bus.subscribe(EventType.EXECUTION_STOPPED, self._on_execution_stopped)
        event_bus.subscribe(
            EventType.EXECUTION_SPEED_CHANGED, self._on_execution_speed_changed
        )

        # Tools: Inspector & Examples
        tools_group = QGroupBox("Tools")
        tools_layout = QHBoxLayout()

        show_examples_btn = QPushButton("Show Examples")
        show_examples_btn.clicked.connect(lambda: self.examples_view.show())
        tools_layout.addWidget(show_examples_btn)

        show_inspector_btn = QPushButton("Show Inspector")
        show_inspector_btn.clicked.connect(lambda: self.inspector_view.show())
        tools_layout.addWidget(show_inspector_btn)

        # Apply layout demo: apply grid layout to demo canvas VM
        apply_layout_btn = QPushButton("Apply Grid Layout (Demo)")

        def _apply_demo_layout():
            self._demo_canvas_vm.apply_layout(algorithm="grid", cols=3, spacing=120)

        apply_layout_btn.clicked.connect(_apply_demo_layout)
        tools_layout.addWidget(apply_layout_btn)

        tools_group.setLayout(tools_layout)
        main_layout.addWidget(tools_group)

        # Instructions
        instructions = QLabel(
            "This demo shows:\n"
            "• Pure Python ViewModels (testable without GUI)\n"
            "• Observable properties (UI auto-updates)\n"
            "• Event bus integration (loose coupling)\n"
            "• CollapsibleSection widget from new framework\n"
            "• Execution controls with full state management"
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)

        main_layout.addStretch()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        print("\n" + "=" * 60)
        print("MVVM GUI Framework Demo Started")
        print("=" * 60)
        print("\nFeatures demonstrated:")
        print("1. Pure Python ViewModels (no PyQt dependencies)")
        print("2. Observable properties with automatic UI updates")
        print("3. Event bus for loose coupling")
        print("4. State store integration (available but not shown)")
        print("5. CollapsibleSection widget from new framework")
        print("6. Execution controls with complete state management")
        print("\nWatch the console for ViewModel/View interaction logs.")
        print("=" * 60 + "\n")

    def _simulate_execution_step(self):
        """Simulate one execution step."""
        # Check if still running
        if self.execution_vm.status != ExecutionStatus.RUNNING:
            self.execution_timer.stop()
            return

        # Increment step
        current = self.execution_vm.current_step
        max_steps = self.execution_vm.max_steps

        if current < max_steps:
            # Simulate step completion by publishing event
            event_bus = get_event_bus()
            event_bus.publish(
                Event(
                    type=EventType.EXECUTION_STEP_COMPLETE,
                    payload={"step": current + 1},
                )
            )
            print(f"[Demo] Execution step {current + 1}/{max_steps} completed")
        else:
            # Execution complete
            self.execution_vm.stop()
            print("[Demo] Execution completed")

    def _on_execution_started(self, event: Event):
        """Handle execution started event."""
        speed_ms = self.execution_vm.speed_ms
        if speed_ms == 0:
            speed_ms = 10  # Min 10ms for max speed to avoid UI freeze

        self.execution_timer.setInterval(speed_ms)
        self.execution_timer.start()
        print(f"[Demo] Execution timer started with interval {speed_ms}ms")

    def _on_execution_paused(self, event: Event):
        """Handle execution paused event."""
        self.execution_timer.stop()
        print("[Demo] Execution timer stopped (paused)")

    def _on_execution_stopped(self, event: Event):
        """Handle execution stopped event."""
        self.execution_timer.stop()
        print("[Demo] Execution timer stopped")

    def _on_execution_speed_changed(self, event: Event):
        """Handle execution speed changed event."""
        if self.execution_vm.status == ExecutionStatus.RUNNING:
            speed_ms = event.payload.get("speed_ms", 100)
            if speed_ms == 0:
                speed_ms = 10  # Min 10ms for max speed
            self.execution_timer.setInterval(speed_ms)
            print(f"[Demo] Execution timer interval updated to {speed_ms}ms")


def main():
    """Run the demo application."""
    if not HAS_PYQT:
        return

    app = QApplication(sys.argv)

    # Initialize framework singletons
    store = get_store()
    event_bus = get_event_bus()

    print(f"State Store initialized: {store}")
    print(f"Event Bus initialized: {event_bus}")

    # Create and show main window
    window = DemoMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
