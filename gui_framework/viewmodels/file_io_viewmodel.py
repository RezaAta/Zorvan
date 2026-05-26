"""
File I/O ViewModel - Pure Python logic for file operations.

Manages file paths, recent files, and file operation state using StateStore.
This ViewModel is completely testable without PyQt dependencies.
"""

from pathlib import Path
from typing import List, Optional

from ..events.bus import Event, EventType
from ..state.store import get_store
from ..viewmodels.base import BaseViewModel, ObservableProperty


class FileIOViewModel(BaseViewModel):
    """ViewModel for file I/O operations.

    Pure Python logic with no PyQt dependencies. Manages current file path,
    recent files list, and file operation state.

    Attributes:
        current_file_path: Path to currently loaded/saved file
        recent_files: List of recently opened files
        is_modified: Whether the current file has unsaved changes
        last_operation: Last file operation performed (new/open/save)
    """

    # Observable properties
    current_file_path = ObservableProperty("current_file_path", default=None)
    recent_files = ObservableProperty("recent_files", default=[])
    is_modified = ObservableProperty("is_modified", default=False)
    last_operation = ObservableProperty("last_operation", default=None)

    # Maximum recent files to track
    MAX_RECENT_FILES = 10

    def __init__(self, **kwargs):
        """Initialize FileIOViewModel.

        Args:
            **kwargs: Forward compatibility for additional init args
        """
        super().__init__()

        self.current_file_path = None
        self.recent_files = []
        self.is_modified = False
        self.last_operation = None

    def initialize(self):
        """Initialize the file I/O ViewModel.

        Load state from state store and subscribe to events.
        """
        # Load from state store if available
        state = self._store.get_state()
        if state and hasattr(state, "file_path"):
            self.current_file_path = state.file_path
            # Load recent files from persistent storage could be added here

    def cleanup(self):
        """Clean up resources."""
        pass

    def set_current_file(self, file_path: Optional[str]):
        """Set the current file path.

        Args:
            file_path: Path to the current file, or None if no file
        """
        self.current_file_path = file_path

        # Update state store
        self._store.update(file_path=file_path)

        # Add to recent files if valid
        if file_path:
            self._add_to_recent_files(file_path)

        # Publish event
        self._event_bus.publish(
            Event(
                type=EventType.FILE_OPENED if file_path else EventType.FILE_CLOSED,
                payload={"file_path": file_path},
            )
        )

    def mark_as_modified(self, modified: bool = True):
        """Mark the current file as modified.

        Args:
            modified: Whether the file is modified
        """
        self.is_modified = modified

    def on_file_new(self):
        """Handle new file operation."""
        self.current_file_path = None
        self.is_modified = False
        self.last_operation = "new"

        # Update state store
        self._store.update(file_path=None)

        # Publish event
        self._event_bus.publish(
            Event(type=EventType.FILE_CLOSED, payload={"operation": "new"})
        )

    def on_file_opened(self, file_path: str):
        """Handle file open operation.

        Args:
            file_path: Path to the opened file
        """
        self.set_current_file(file_path)
        self.is_modified = False
        self.last_operation = "open"

        # Publish event
        self._event_bus.publish(
            Event(
                type=EventType.FILE_OPENED,
                payload={"file_path": file_path, "operation": "open"},
            )
        )

    def on_file_saved(self, file_path: str):
        """Handle file save operation.

        Args:
            file_path: Path where the file was saved
        """
        self.set_current_file(file_path)
        self.is_modified = False
        self.last_operation = "save"

        # Publish event
        self._event_bus.publish(
            Event(
                type=EventType.FILE_SAVED,
                payload={"file_path": file_path, "operation": "save"},
            )
        )

    def get_file_name(self) -> str:
        """Get the current file name (without path).

        Returns:
            File name, or "Untitled" if no file
        """
        if not self.current_file_path:
            return "Untitled"

        try:
            return Path(self.current_file_path).name
        except Exception:
            return "Untitled"

    def get_file_extension(self) -> str:
        """Get the current file extension.

        Returns:
            File extension (e.g., ".drawio"), or empty string if no file
        """
        if not self.current_file_path:
            return ""

        try:
            return Path(self.current_file_path).suffix
        except Exception:
            return ""

    def is_cgjson_file(self) -> bool:
        """Check if current file is a CGJson file.

        Returns:
            True if current file is .cgjson, .cgz, or .json
        """
        ext = self.get_file_extension().lower()
        return ext in [".cgjson", ".cgz", ".json"]

    def get_recent_files(self) -> List[str]:
        """Get list of recent files.

        Returns:
            List of recent file paths
        """
        return list(self.recent_files)

    def clear_recent_files(self):
        """Clear the recent files list."""
        self.recent_files = []

    def _add_to_recent_files(self, file_path: str):
        """Add a file to the recent files list.

        Args:
            file_path: Path to add to recent files
        """
        # Create new list to trigger property change
        new_recent = list(self.recent_files)

        # Remove if already in list
        if file_path in new_recent:
            new_recent.remove(file_path)

        # Add to front
        new_recent.insert(0, file_path)

        # Limit to MAX_RECENT_FILES
        if len(new_recent) > self.MAX_RECENT_FILES:
            new_recent = new_recent[: self.MAX_RECENT_FILES]

        # Update property
        self.recent_files = new_recent

    @property
    def has_file(self) -> bool:
        """Check if there is a current file.

        Returns:
            True if there is a current file
        """
        return self.current_file_path is not None

    @property
    def can_save(self) -> bool:
        """Check if save operation is available.

        Returns:
            True if can save (has file and is modified)
        """
        return self.has_file and self.is_modified

    @property
    def window_title(self) -> str:
        """Get the window title based on current file.

        Returns:
            Window title string
        """
        title = self.get_file_name()
        if self.is_modified:
            title += " *"
        return title
