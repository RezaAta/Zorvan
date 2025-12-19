"""
ExecutionView: PyQt6 UI for execution controls.

This view provides the user interface for controlling graph execution,
binding to ExecutionViewModel for reactive state management.
"""

from enum import Enum

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QCheckBox,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSlider,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

    # Minimal stubs for testing without PyQt6
    class QWidget:
        def __init__(self, parent=None):
            pass

    class _Orientation:
        Horizontal = 1

    class Qt:
        Orientation = _Orientation()


from ..viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from .base import BaseView

    class ExecutionView(BaseView):
        """
        PyQt6 view for execution controls.

        Features:
        - Play/Pause/Resume/Step/Reset/Stop buttons
        - Speed control slider with max speed toggle
        - Max steps configuration
        - Status display
        - Automatic button state management based on execution state

        Example:
            >>> vm = ExecutionViewModel(max_steps=1000, speed_ms=100)
            >>> view = ExecutionView(vm, parent=main_window)
            >>> view.show()
        """

        def __init__(self, viewmodel: BaseViewModel, parent: QWidget = None):
            """
            Initialize ExecutionView.

            Args:
                viewmodel: ExecutionViewModel instance
                parent: Parent Qt widget
            """
            super().__init__(viewmodel, parent)
            self._setup_ui()

        def _setup_ui(self):
            """Create and layout the UI widgets."""
            layout = QVBoxLayout(self)

            # Status group
            status_group = QGroupBox("Execution Status")
            status_layout = QVBoxLayout()

            self.status_label = QLabel("Status: IDLE")
            status_layout.addWidget(self.status_label)

            self.step_label = QLabel("Step: 0 / 1000")
            status_layout.addWidget(self.step_label)

            status_group.setLayout(status_layout)
            layout.addWidget(status_group)

            # Control buttons group
            controls_group = QGroupBox("Controls")
            controls_layout = QVBoxLayout()

            # Main control buttons (horizontal row)
            buttons_layout = QHBoxLayout()

            self.play_button = QPushButton("▶ Play")
            self.play_button.clicked.connect(self._on_play_clicked)
            buttons_layout.addWidget(self.play_button)

            self.pause_button = QPushButton("⏸ Pause")
            self.pause_button.clicked.connect(self._on_pause_clicked)
            buttons_layout.addWidget(self.pause_button)

            self.resume_button = QPushButton("⏵ Resume")
            self.resume_button.clicked.connect(self._on_resume_clicked)
            buttons_layout.addWidget(self.resume_button)

            self.step_button = QPushButton("⏭ Step")
            self.step_button.clicked.connect(self._on_step_clicked)
            buttons_layout.addWidget(self.step_button)

            controls_layout.addLayout(buttons_layout)

            # Secondary control buttons (horizontal row)
            secondary_buttons_layout = QHBoxLayout()

            self.reset_button = QPushButton("⏮ Reset")
            self.reset_button.clicked.connect(self._on_reset_clicked)
            secondary_buttons_layout.addWidget(self.reset_button)

            self.stop_button = QPushButton("⏹ Stop")
            self.stop_button.clicked.connect(self._on_stop_clicked)
            secondary_buttons_layout.addWidget(self.stop_button)

            controls_layout.addLayout(secondary_buttons_layout)

            controls_group.setLayout(controls_layout)
            layout.addWidget(controls_group)

            # Speed control group
            speed_group = QGroupBox("Speed Control")
            speed_layout = QVBoxLayout()

            # Speed slider
            speed_slider_layout = QHBoxLayout()
            speed_slider_layout.addWidget(QLabel("Speed (ms):"))

            self.speed_slider = QSlider(Qt.Orientation.Horizontal)
            self.speed_slider.setMinimum(0)
            self.speed_slider.setMaximum(1000)
            self.speed_slider.setValue(100)
            self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.speed_slider.setTickInterval(100)
            self.speed_slider.valueChanged.connect(self._on_speed_changed)
            speed_slider_layout.addWidget(self.speed_slider)

            self.speed_value_label = QLabel("100 ms")
            speed_slider_layout.addWidget(self.speed_value_label)

            speed_layout.addLayout(speed_slider_layout)

            # Max speed checkbox
            self.max_speed_checkbox = QCheckBox("Max Speed (no delay)")
            self.max_speed_checkbox.stateChanged.connect(self._on_max_speed_toggled)
            speed_layout.addWidget(self.max_speed_checkbox)

            speed_group.setLayout(speed_layout)
            layout.addWidget(speed_group)

            # Configuration group
            config_group = QGroupBox("Configuration")
            config_layout = QHBoxLayout()

            config_layout.addWidget(QLabel("Max Steps:"))

            self.max_steps_spinbox = QSpinBox()
            self.max_steps_spinbox.setMinimum(1)
            self.max_steps_spinbox.setMaximum(1000000)
            self.max_steps_spinbox.setValue(1000)
            self.max_steps_spinbox.valueChanged.connect(self._on_max_steps_changed)
            config_layout.addWidget(self.max_steps_spinbox)

            config_layout.addStretch()

            config_group.setLayout(config_layout)
            layout.addWidget(config_group)

            layout.addStretch()

        def _bind_viewmodel(self):
            """Bind to ViewModel observable properties."""
            # Observe status changes
            self._viewmodel.observe_property("status", self._on_status_changed)

            # Observe step changes
            self._viewmodel.observe_property(
                "current_step", self._on_current_step_changed
            )
            self._viewmodel.observe_property("max_steps", self._on_max_steps_vm_changed)

            # Observe speed changes
            self._viewmodel.observe_property("speed_ms", self._on_speed_vm_changed)
            self._viewmodel.observe_property(
                "is_max_speed", self._on_is_max_speed_changed
            )

            # Initialize UI with current ViewModel state
            self._update_button_states()
            self._update_status_display()
            self._update_step_display()
            self._update_speed_display()

        # ViewModel change handlers

        def _on_status_changed(self, old_value, new_value):
            """Handle execution status changes from ViewModel."""
            self._update_button_states()
            self._update_status_display()

        def _on_current_step_changed(self, old_value, new_value):
            """Handle current step changes from ViewModel."""
            self._update_step_display()

        def _on_max_steps_vm_changed(self, old_value, new_value):
            """Handle max steps changes from ViewModel."""
            # Update spinbox if needed (avoid circular updates)
            if self.max_steps_spinbox.value() != new_value:
                self.max_steps_spinbox.blockSignals(True)
                self.max_steps_spinbox.setValue(new_value)
                self.max_steps_spinbox.blockSignals(False)
            self._update_step_display()

        def _on_speed_vm_changed(self, old_value, new_value):
            """Handle speed changes from ViewModel."""
            # Update slider if needed (avoid circular updates)
            if self.speed_slider.value() != new_value:
                self.speed_slider.blockSignals(True)
                self.speed_slider.setValue(new_value)
                self.speed_slider.blockSignals(False)
            self._update_speed_display()

        def _on_is_max_speed_changed(self, old_value, new_value):
            """Handle max speed toggle changes from ViewModel."""
            # Update checkbox if needed (avoid circular updates)
            if self.max_speed_checkbox.isChecked() != new_value:
                self.max_speed_checkbox.blockSignals(True)
                self.max_speed_checkbox.setChecked(new_value)
                self.max_speed_checkbox.blockSignals(False)

            # Enable/disable slider based on max speed
            self.speed_slider.setEnabled(not new_value)
            self._update_speed_display()

        # UI update methods

        def _update_button_states(self):
            """Update button enabled states based on execution state."""
            self.play_button.setEnabled(self._viewmodel.can_play)
            self.pause_button.setEnabled(self._viewmodel.can_pause)
            self.resume_button.setEnabled(self._viewmodel.can_resume)
            self.step_button.setEnabled(self._viewmodel.can_step)
            self.reset_button.setEnabled(self._viewmodel.can_reset)
            self.stop_button.setEnabled(
                self._viewmodel.is_running or self._viewmodel.is_paused
            )

        def _update_status_display(self):
            """Update status label text."""
            status_text = str(self._viewmodel.status).replace("ExecutionStatus.", "")
            self.status_label.setText(f"Status: {status_text}")

        def _update_step_display(self):
            """Update step counter display."""
            self.step_label.setText(
                f"Step: {self._viewmodel.current_step} / {self._viewmodel.max_steps}"
            )

        def _update_speed_display(self):
            """Update speed display label."""
            if self._viewmodel.is_max_speed:
                self.speed_value_label.setText("MAX")
            else:
                self.speed_value_label.setText(f"{self._viewmodel.speed_ms} ms")

        # User interaction handlers

        def _on_play_clicked(self):
            """Handle Play button click."""
            self._viewmodel.play()

        def _on_pause_clicked(self):
            """Handle Pause button click."""
            self._viewmodel.pause()

        def _on_resume_clicked(self):
            """Handle Resume button click."""
            self._viewmodel.resume()

        def _on_step_clicked(self):
            """Handle Step button click."""
            self._viewmodel.step()

        def _on_reset_clicked(self):
            """Handle Reset button click."""
            self._viewmodel.reset()

        def _on_stop_clicked(self):
            """Handle Stop button click."""
            self._viewmodel.stop()

        def _on_speed_changed(self, value: int):
            """Handle speed slider value change."""
            self._viewmodel.set_speed(value)

        def _on_max_speed_toggled(self, state: int):
            """Handle max speed checkbox toggle."""
            self._viewmodel.toggle_max_speed()

        def _on_max_steps_changed(self, value: int):
            """Handle max steps spinbox change."""
            self._viewmodel.max_steps = value

else:
    # Minimal stub for testing without PyQt6
    class ExecutionView:
        """Stub ExecutionView for testing without PyQt6."""

        def __init__(self, viewmodel, parent=None):
            self._viewmodel = viewmodel
            self.parent = parent

        def show(self):
            pass
