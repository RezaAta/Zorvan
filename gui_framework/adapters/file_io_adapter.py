"""
File I/O Adapter - Bridges MVVM FileIOViewModel with legacy FileIOController.

This adapter enables incremental migration from the legacy file I/O controller
to the MVVM pattern by translating between the two systems.
"""

import logging
from typing import TYPE_CHECKING, Optional

from ..events.bus import Event, EventType, get_event_bus
from ..viewmodels.file_io_viewmodel import FileIOViewModel

if TYPE_CHECKING:
    from zorvan.GUI.controllers.file_io_controller import FileIOController
    from zorvan.GUI.main_window import MainWindow

logger = logging.getLogger(__name__)


class FileIOAdapter:
    """
    Adapter that bridges MVVM FileIOViewModel with legacy FileIOController.

    This allows the new MVVM components to track file state while
    the legacy controller handles actual file operations.

    Usage:
        adapter = FileIOAdapter(main_window)
        adapter.connect()  # Wire up signals

        # Now file operations update MVVM state
    """

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize the file I/O adapter.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window
        self.event_bus = get_event_bus()

        # Create the MVVM ViewModel
        self.viewmodel = FileIOViewModel()
        self.viewmodel.initialize()

    @property
    def file_io_controller(self) -> Optional["FileIOController"]:
        """Access the legacy file I/O controller."""
        return getattr(self.main_window, "file_io_controller", None)

    def connect(self):
        """Wire up event subscriptions between MVVM and legacy systems."""
        # Subscribe to MVVM events and forward to legacy
        self.event_bus.subscribe(EventType.FILE_OPENED, self._on_file_opened_event)
        self.event_bus.subscribe(EventType.FILE_SAVED, self._on_file_saved_event)
        self.event_bus.subscribe(EventType.FILE_CLOSED, self._on_file_closed_event)

        logger.debug("FileIOAdapter connected")

    def disconnect(self):
        """Unsubscribe from events."""
        self.event_bus.unsubscribe(EventType.FILE_OPENED, self._on_file_opened_event)
        self.event_bus.unsubscribe(EventType.FILE_SAVED, self._on_file_saved_event)
        self.event_bus.unsubscribe(EventType.FILE_CLOSED, self._on_file_closed_event)

        # Cleanup viewmodel
        try:
            self.viewmodel.cleanup()
        except Exception:
            pass

        logger.debug("FileIOAdapter disconnected")

    # Event handlers

    def _on_file_opened_event(self, event: Event):
        """Handle file opened event."""
        payload = event.payload or {}
        file_path = payload.get("file_path")
        if file_path:
            self._update_window_title(file_path)

    def _on_file_saved_event(self, event: Event):
        """Handle file saved event."""
        payload = event.payload or {}
        file_path = payload.get("file_path")
        if file_path:
            self._update_window_title(file_path)

    def _on_file_closed_event(self, event: Event):
        """Handle file closed event."""
        self._update_window_title(None)

    def _update_window_title(self, file_path: Optional[str]):
        """Update main window title to reflect current file."""
        try:
            base_title = "Zorvan"
            if file_path:
                file_name = self.viewmodel.get_file_name()
                self.main_window.setWindowTitle(f"{file_name} - {base_title}")
            else:
                self.main_window.setWindowTitle(f"Untitled - {base_title}")
        except Exception as e:
            logger.debug("Could not update window title: %s", e)

    # Public API - called by legacy controller to notify MVVM

    def notify_file_opened(self, file_path: str):
        """Notify that a file was opened (called by legacy controller)."""
        self.viewmodel.on_file_opened(file_path)

    def notify_file_saved(self, file_path: str):
        """Notify that a file was saved (called by legacy controller)."""
        self.viewmodel.on_file_saved(file_path)

    def notify_new_graph(self):
        """Notify that a new graph was created (called by legacy controller)."""
        self.viewmodel.on_file_new()

    def notify_modified(self, modified: bool = True):
        """Notify that the graph was modified."""
        self.viewmodel.mark_as_modified(modified)
        self._update_window_title_modified()

    def _update_window_title_modified(self):
        """Update window title to show modified indicator."""
        try:
            if self.viewmodel.is_modified:
                current_title = self.main_window.windowTitle()
                if not current_title.startswith("*"):
                    self.main_window.setWindowTitle(f"*{current_title}")
        except Exception:
            pass

    # Properties for external access

    @property
    def current_file_path(self) -> Optional[str]:
        """Get the current file path."""
        return self.viewmodel.current_file_path

    @property
    def is_modified(self) -> bool:
        """Check if current file has unsaved changes."""
        return self.viewmodel.is_modified

    @property
    def recent_files(self):
        """Get list of recent files."""
        return self.viewmodel.get_recent_files()
