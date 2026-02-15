"""
ExecutionView: PyQt6 UI for execution controls.

This view provides the user interface for controlling graph execution,
binding to ExecutionViewModel for reactive state management.
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
    from PyQt6.QtWidgets import (
        QCheckBox,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QSlider,
        QSpinBox,
        QStyle,
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


# Icon helper functions for themed icons
def _get_accent_color() -> str:
    """Get the current accent color from the theme manager."""
    try:
        from ComputationalGraphs.GUI.theme import get_theme_manager

        tm = get_theme_manager()
        return tm.get_color("accent", "#4a86e8").name()
    except Exception:
        return "#4a86e8"


def _tint_pixmap(pixmap: "QPixmap", color: str) -> "QPixmap":
    """Return a copy of pixmap tinted with the given color."""
    if not PYQT_AVAILABLE or pixmap.isNull():
        return pixmap
    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setCompositionMode(QPainter.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(result.rect(), QColor(color))
    painter.end()
    return result


def _create_themed_icon(fa_name: str, fallback_pixmap, size_px: int = 16) -> "QIcon":
    """Create a themed icon using qtawesome with accent color, or fallback."""
    color = _get_accent_color()

    # Try qtawesome first
    try:
        import qtawesome as qta

        return qta.icon(fa_name, color=color)
    except Exception:
        pass

    # Fallback to QStyle pixmap tinted with accent color
    try:
        if fallback_pixmap is not None and PYQT_AVAILABLE:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                style = app.style()
                pm = style.standardIcon(fallback_pixmap).pixmap(QSize(size_px, size_px))
                return QIcon(_tint_pixmap(pm, color))
    except Exception:
        pass

    # Last resort: synthesize a colored pixmap
    try:
        pm = QPixmap(size_px, size_px)
        pm.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pm)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, size_px - 4, size_px - 4)
        painter.end()
        return QIcon(pm)
    except Exception:
        return QIcon()


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
            layout.setContentsMargins(0, 0, 0, 0)

            # Step counter label (matches legacy: "Step: 0 / max")
            self.step_label = QLabel("Step: 0 / 100")
            layout.addWidget(self.step_label)

            # Progress bar for execution progress (matches legacy step_progress)
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(False)
            layout.addWidget(self.progress_bar)

            # Main control buttons (horizontal row) - matches legacy layout
            buttons_layout = QHBoxLayout()

            # Play/Start button with themed icon
            self.play_button = QPushButton("Start")
            try:
                self.play_button.setProperty("themed", True)
            except Exception:
                pass
            self._apply_themed_icon(
                self.play_button, "fa5s.play", QStyle.StandardPixmap.SP_MediaPlay, 16
            )
            self.play_button.clicked.connect(self._on_play_clicked)
            buttons_layout.addWidget(self.play_button)

            # Pause button with themed icon
            self.pause_button = QPushButton("Pause")
            try:
                self.pause_button.setProperty("themed", True)
            except Exception:
                pass
            self._apply_themed_icon(
                self.pause_button, "fa5s.pause", QStyle.StandardPixmap.SP_MediaPause, 16
            )
            self.pause_button.clicked.connect(self._on_pause_clicked)
            self.pause_button.setEnabled(False)
            buttons_layout.addWidget(self.pause_button)

            # Resume button with themed icon
            self.resume_button = QPushButton("Resume")
            try:
                self.resume_button.setProperty("themed", True)
            except Exception:
                pass
            self._apply_themed_icon(
                self.resume_button, "fa5s.play", QStyle.StandardPixmap.SP_MediaPlay, 16
            )
            self.resume_button.clicked.connect(self._on_resume_clicked)
            self.resume_button.setEnabled(False)
            buttons_layout.addWidget(self.resume_button)

            # Step button moved next to Resume to match requested layout
            self.step_button = QPushButton("Step")
            try:
                self.step_button.setProperty("themed", True)
            except Exception:
                pass
            self._apply_themed_icon(
                self.step_button,
                "fa5s.step-forward",
                QStyle.StandardPixmap.SP_ArrowRight,
                14,
            )
            self.step_button.clicked.connect(self._on_step_clicked)
            buttons_layout.addWidget(self.step_button)

            layout.addLayout(buttons_layout)

            # Reset controls row (matches legacy: Restore, Reset Proc, Reset All)
            reset_row = QHBoxLayout()

            self.restore_button = QPushButton("Restore")
            try:
                self.restore_button.setProperty("themed", True)
            except Exception:
                pass
            self._apply_themed_icon(
                self.restore_button,
                "fa5s.undo",
                QStyle.StandardPixmap.SP_BrowserReload,
                14,
            )
            self.restore_button.setToolTip(
                "Restore graph to iteration 0 state (node values) without changing iteration counter"
            )
            self.restore_button.clicked.connect(self._on_restore_clicked)
            reset_row.addWidget(self.restore_button)

            self.stop_button = QPushButton("Reset Proc")
            try:
                self.stop_button.setProperty("themed", True)
            except Exception:
                pass
            self._apply_themed_icon(
                self.stop_button, "fa5s.stop", QStyle.StandardPixmap.SP_MediaStop, 14
            )
            self.stop_button.setToolTip(
                "Reset iteration counter to 0 and reinitialize processor (preserves node values)"
            )
            self.stop_button.clicked.connect(self._on_stop_clicked)
            reset_row.addWidget(self.stop_button)

            self.reset_button = QPushButton("Reset All")
            try:
                self.reset_button.setProperty("themed", True)
            except Exception:
                pass
            self._apply_themed_icon(
                self.reset_button,
                "fa5s.sync",
                QStyle.StandardPixmap.SP_DialogResetButton,
                14,
            )
            self.reset_button.setToolTip(
                "Full reset: restore graph to iteration 0 AND reset processor/counter"
            )
            self.reset_button.clicked.connect(self._on_reset_clicked)
            reset_row.addWidget(self.reset_button)

            layout.addLayout(reset_row)

            # Rebuild button (matches legacy)
            self.rebuild_button = QPushButton("Rebuild")
            try:
                self.rebuild_button.setProperty("themed", True)
            except Exception:
                pass
            self.rebuild_button.setToolTip("Rebuild graph from canvas")
            self.rebuild_button.clicked.connect(self._on_rebuild_clicked)
            layout.addWidget(self.rebuild_button)

            # Subscribe to theme changes to update icons
            self._connect_theme_updates()

        def _apply_themed_icon(
            self, button: QPushButton, fa_name: str, fallback, size_px: int = 16
        ):
            """Apply a themed icon to a button with accent color."""
            try:
                icon = _create_themed_icon(fa_name, fallback, size_px)
                button.setIcon(icon)
                button.setIconSize(QSize(size_px, size_px))
                try:
                    button.setProperty("themed", True)
                except Exception:
                    pass
                # Store icon info for theme updates
                if not hasattr(self, "_themed_buttons"):
                    self._themed_buttons = []
                self._themed_buttons.append((button, fa_name, fallback, size_px))
            except Exception as e:
                logger.debug("Could not apply themed icon: %s", e)

        def _connect_theme_updates(self):
            """Connect to theme manager to refresh icons on theme change."""
            try:
                from ComputationalGraphs.GUI.theme import get_theme_manager

                tm = get_theme_manager()
                tm.theme_changed.connect(self._refresh_icons)
            except Exception:
                pass

        def _refresh_icons(self):
            """Refresh all button icons when theme changes."""
            if hasattr(self, "_themed_buttons"):
                for button, fa_name, fallback, size_px in self._themed_buttons:
                    try:
                        icon = _create_themed_icon(fa_name, fallback, size_px)
                        button.setIcon(icon)
                    except Exception:
                        pass

        def _bind_viewmodel(self):
            """Bind to ViewModel observable properties."""
            # Observe status changes
            self._viewmodel.observe_property("status", self._on_status_changed)

            # Observe step changes
            self._viewmodel.observe_property(
                "current_step", self._on_current_step_changed
            )
            self._viewmodel.observe_property("max_steps", self._on_max_steps_vm_changed)

            # Initialize UI with current ViewModel state
            self._update_button_states()
            self._update_step_display()

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
            self._update_step_display()
            # Update progress bar maximum
            self.progress_bar.setMaximum(new_value)

        # UI update methods

        def _update_button_states(self):
            """Update button enabled states based on execution state."""
            self.play_button.setEnabled(self._viewmodel.can_play)
            self.pause_button.setEnabled(self._viewmodel.can_pause)
            self.resume_button.setEnabled(self._viewmodel.can_resume)
            self.step_button.setEnabled(self._viewmodel.can_step)
            self.reset_button.setEnabled(self._viewmodel.can_reset)
            # Stop button renamed to reset_proc in new UI
            self.stop_button.setEnabled(
                self._viewmodel.is_running or self._viewmodel.is_paused
            )

        def _update_step_display(self):
            """Update step counter and progress bar display."""
            current = self._viewmodel.current_step
            maximum = self._viewmodel.max_steps
            self.step_label.setText(f"Step: {current} / {maximum}")
            # Update progress bar
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(current)

        def _update_status_display(self):
            """Update the status display based on current execution status."""
            status = self._viewmodel.status
            # Update progress bar style based on status
            if status == "running":
                self.progress_bar.setStyleSheet("")  # Default style
            elif status == "paused":
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background-color: #f39c12; }"
                )
            elif status == "stopped" or status == "idle":
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background-color: #3498db; }"
                )

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
            """Handle Reset All button click - full reset: restore graph AND reset processor."""
            self._viewmodel.reset()
            # Also forward to main window's reset_graph for full reset
            self._call_main_window_method("reset_graph")

        def _on_stop_clicked(self):
            """Handle Reset Processor button click - reset iteration counter only."""
            self._viewmodel.stop()
            # Forward to main window's reset_processor
            self._call_main_window_method("reset_processor")

        def _on_restore_clicked(self):
            """Handle Restore button click - restore graph values without changing counter."""
            # Forward to main window's restore_graph
            self._call_main_window_method("restore_graph")

        def _on_rebuild_clicked(self):
            """Handle Rebuild button click."""
            # Forward to main window's rebuild_graph
            self._call_main_window_method("rebuild_graph")

        def _call_main_window_method(self, method_name: str):
            """Helper to call a method on the main window."""
            try:
                if hasattr(self, "parent") and self.parent():
                    parent = self.parent()
                    # Direct method on parent
                    if hasattr(parent, method_name):
                        getattr(parent, method_name)()
                        return
                    # Try parent.main_window
                    if hasattr(parent, "main_window") and hasattr(
                        parent.main_window, method_name
                    ):
                        getattr(parent.main_window, method_name)()
                        return
                    # Walk up the parent chain to find MainWindow
                    widget = parent
                    while widget is not None:
                        if hasattr(widget, method_name):
                            getattr(widget, method_name)()
                            return
                        widget = (
                            widget.parent()
                            if hasattr(widget, "parent") and callable(widget.parent)
                            else None
                        )
            except Exception as e:
                logger.debug("Could not call %s: %s", method_name, e)

else:
    # Minimal stub for testing without PyQt6
    class ExecutionView:
        """Stub ExecutionView for testing without PyQt6."""

        def __init__(self, viewmodel, parent=None):
            self._viewmodel = viewmodel
            self.parent = parent

        def show(self):
            pass
