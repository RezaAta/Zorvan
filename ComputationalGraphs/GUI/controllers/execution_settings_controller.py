"""
ExecutionSettingsController - Manages execution speed and display settings.

Extracted from MainWindow as part of Clean Code refactoring.
Handles speed slider/spinbox, max speed toggle, verbose output, and related settings.
"""

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ExecutionSettingsController:
    """Controller for execution speed and display settings."""

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window

    def on_speed_changed(self, value: int):
        """Handle speed slider change.

        Args:
            value: New speed value in milliseconds
        """
        mw = self.main_window

        # Keep spinbox in sync when slider moves
        try:
            if hasattr(mw, "speed_spin") and mw.speed_spin.value() != value:
                mw.speed_spin.blockSignals(True)
                mw.speed_spin.setValue(value)
                mw.speed_spin.blockSignals(False)
        except Exception:
            pass

        mw.speed_label.setText(f"{value} ms")
        mw.graph_runner.set_speed(value)

    def on_speed_spin_changed(self, value: int):
        """Handle speed spinbox (typed) change.

        Args:
            value: New speed value in milliseconds
        """
        mw = self.main_window

        # Keep slider in sync when spinbox changes
        try:
            if hasattr(mw, "speed_slider") and mw.speed_slider.value() != value:
                mw.speed_slider.blockSignals(True)
                mw.speed_slider.setValue(value)
                mw.speed_slider.blockSignals(False)
        except Exception:
            pass

        mw.speed_label.setText(f"{value} ms")
        mw.graph_runner.set_speed(value)

    def on_max_speed_toggled(self, checked: bool):
        """Handle max speed button toggle.

        Args:
            checked: True if max speed is enabled
        """
        mw = self.main_window

        if checked:
            # Save current delay and set to 0ms (maximum speed)
            mw.saved_speed = mw.speed_slider.value()
            mw.speed_slider.setEnabled(False)
            if hasattr(mw, "speed_spin"):
                mw.speed_spin.setEnabled(False)
            mw.graph_runner.set_speed(0)
            mw.speed_label.setText("0 ms (MAX)")
            # Remove emoji from button text; keep state description
            mw.max_speed_btn.setText("Max Speed (ON)")
        else:
            # Restore previous speed
            mw.speed_slider.setEnabled(True)
            if hasattr(mw, "speed_spin"):
                mw.speed_spin.setEnabled(True)

            restore_speed = getattr(mw, "saved_speed", 500)  # Default to 500 if not set

            # Restore both slider and spinbox without re-trigger loops
            try:
                mw.speed_slider.blockSignals(True)
                mw.speed_slider.setValue(restore_speed)
                mw.speed_slider.blockSignals(False)
            except Exception:
                mw.speed_slider.setValue(restore_speed)

            try:
                if hasattr(mw, "speed_spin"):
                    mw.speed_spin.blockSignals(True)
                    mw.speed_spin.setValue(restore_speed)
                    mw.speed_spin.blockSignals(False)
            except Exception:
                pass

            mw.graph_runner.set_speed(restore_speed)
            mw.speed_label.setText(f"{restore_speed} ms")
            mw.max_speed_btn.setText("Max Speed (0ms)")

    def on_verbose_changed(self, state: int):
        """Handle verbose checkbox change.

        Args:
            state: Qt checkbox state value
        """
        mw = self.main_window
        verbose_enabled = state == Qt.CheckState.Checked.value

        # Update the graph processor's verbose flag
        if mw.graph_runner and mw.graph_runner.graph_processor:
            mw.graph_runner.graph_processor.verbose = verbose_enabled

            if verbose_enabled:
                mw.status_bar.showMessage("Verbose output enabled - check terminal")
            else:
                mw.status_bar.showMessage("Verbose output disabled")

        # Also write to console if available
        try:
            mw.write_to_console(
                f"Verbose {'enabled' if verbose_enabled else 'disabled'}",
                verbose_only=False,
            )
        except Exception:
            pass

    def on_processor_type_changed(self, index: int):
        """Handle processor type selection change.

        Args:
            index: Combo box index (0=forward, 1=concurrent, 2=manual)
        """
        mw = self.main_window

        # Map combo index: 0 -> forward, 1 -> concurrent, 2 -> manual
        processor_type = (
            "forward" if index == 0 else ("concurrent" if index == 1 else "manual")
        )
        mw.graph_runner.set_processor_type(processor_type)

        # Show/hide forward and manual processing panels based on mode
        is_forward_mode = index == 0
        is_manual_mode = index == 2
        is_sequence_mode = (
            is_forward_mode or is_manual_mode
        )  # Both use ManualProcessing

        # Threading combo only relevant for concurrent mode
        try:
            mw.threading_combo.setEnabled(index == 1)
        except Exception:
            pass

        # Starting/stopping nodes panel for forward and manual processing
        if (
            hasattr(mw, "starting_nodes_widget")
            and mw.starting_nodes_widget is not None
        ):
            mw.starting_nodes_widget.setVisible(is_sequence_mode)

        if (
            hasattr(mw, "stopping_nodes_widget")
            and mw.stopping_nodes_widget is not None
        ):
            mw.stopping_nodes_widget.setVisible(is_forward_mode)

        # Manual sequence panel for manual processing
        if (
            hasattr(mw, "manual_sequence_widget")
            and mw.manual_sequence_widget is not None
        ):
            mw.manual_sequence_widget.setVisible(is_manual_mode)

        mode_name = processor_type.replace("_", " ").title()
        mw.status_bar.showMessage(f"Processor type: {mode_name}")

        # Update starting nodes display when switching to sequence-based modes
        if is_sequence_mode:
            try:
                mw.update_starting_nodes_display()
            except Exception:
                pass
        if is_forward_mode:
            try:
                mw.update_stopping_nodes_display()
            except Exception:
                pass

        # When switching to Manual Processing, show sequence from graph
        if is_manual_mode:
            try:
                mw.load_manual_sequence_from_graph()
            except Exception:
                pass

    def on_threading_mode_changed(self, index: int):
        """Handle threading mode selection change.

        Args:
            index: Combo box index (0=single thread, 1=multi thread)
        """
        mw = self.main_window
        use_multithreading = index == 1  # 0 = Single Thread, 1 = Multi Thread
        mw.graph_runner.set_threading_mode(use_multithreading)
        mode_name = "Multi-threaded" if use_multithreading else "Single-threaded"
        mw.status_bar.showMessage(f"Processing mode: {mode_name}")
