"""
Unit tests for FileIOViewModel.

Tests the pure Python logic of file I/O management without any GUI dependencies.
"""

import pytest

from gui_framework.viewmodels.file_io_viewmodel import FileIOViewModel
from gui_framework.events.bus import EventType


class TestFileIOViewModel:
    """Test suite for FileIOViewModel."""

    def test_initialization(self):
        """Test ViewModel initializes with default values."""
        vm = FileIOViewModel()
        vm.initialize()

        assert vm.current_file_path is None
        assert vm.recent_files == []
        assert vm.is_modified is False
        assert vm.last_operation is None
        assert vm.has_file is False

        vm.cleanup()

    def test_set_current_file(self):
        """Test setting current file path."""
        vm = FileIOViewModel()
        vm.initialize()

        vm.set_current_file("/path/to/file.drawio")

        assert vm.current_file_path == "/path/to/file.drawio"
        assert vm.has_file is True
        assert "/path/to/file.drawio" in vm.recent_files

        vm.cleanup()

    def test_set_current_file_none(self):
        """Test setting current file to None."""
        vm = FileIOViewModel()
        vm.initialize()

        vm.set_current_file("/path/to/file.drawio")
        vm.set_current_file(None)

        assert vm.current_file_path is None
        assert vm.has_file is False

        vm.cleanup()

    def test_mark_as_modified(self):
        """Test marking file as modified."""
        vm = FileIOViewModel()
        vm.initialize()

        vm.set_current_file("/path/to/file.drawio")
        vm.mark_as_modified(True)

        assert vm.is_modified is True
        assert vm.can_save is True

        vm.mark_as_modified(False)
        assert vm.is_modified is False
        assert vm.can_save is False

        vm.cleanup()

    def test_on_file_new(self):
        """Test new file operation."""
        vm = FileIOViewModel()
        vm.initialize()

        # Start with a file
        vm.set_current_file("/path/to/file.drawio")
        vm.mark_as_modified(True)

        # New file
        vm.on_file_new()

        assert vm.current_file_path is None
        assert vm.is_modified is False
        assert vm.last_operation == "new"

        vm.cleanup()

    def test_on_file_opened(self):
        """Test file open operation."""
        vm = FileIOViewModel()
        vm.initialize()

        vm.on_file_opened("/path/to/opened.drawio")

        assert vm.current_file_path == "/path/to/opened.drawio"
        assert vm.is_modified is False
        assert vm.last_operation == "open"

        vm.cleanup()

    def test_on_file_saved(self):
        """Test file save operation."""
        vm = FileIOViewModel()
        vm.initialize()

        vm.set_current_file("/path/to/file.drawio")
        vm.mark_as_modified(True)

        vm.on_file_saved("/path/to/file.drawio")

        assert vm.is_modified is False
        assert vm.last_operation == "save"

        vm.cleanup()

    def test_get_file_name(self):
        """Test getting file name."""
        vm = FileIOViewModel()
        vm.initialize()

        # Reset state
        vm._store.update(file_path=None)
        vm.current_file_path = None

        # No file
        assert vm.get_file_name() == "Untitled"

        # With file
        vm.set_current_file("/path/to/my_graph.drawio")
        assert vm.get_file_name() == "my_graph.drawio"

        vm.cleanup()

    def test_get_file_extension(self):
        """Test getting file extension."""
        vm = FileIOViewModel()
        vm.initialize()

        # Reset state
        vm._store.update(file_path=None)
        vm.current_file_path = None

        # No file
        assert vm.get_file_extension() == ""

        # With .drawio file
        vm.set_current_file("/path/to/file.drawio")
        assert vm.get_file_extension() == ".drawio"

        # With .cgjson file
        vm.set_current_file("/path/to/file.cgjson")
        assert vm.get_file_extension() == ".cgjson"

        vm.cleanup()

    def test_is_drawio_file(self):
        """Test detecting Draw.io files."""
        vm = FileIOViewModel()
        vm.initialize()

        # Reset state
        vm._store.update(file_path=None)

        # No file
        assert vm.is_drawio_file() is False

        # Draw.io file
        vm.set_current_file("/path/to/file.drawio")
        assert vm.is_drawio_file() is True

        # XML file
        vm.set_current_file("/path/to/file.xml")
        assert vm.is_drawio_file() is True

        # Other file
        vm.set_current_file("/path/to/file.cgjson")
        assert vm.is_drawio_file() is False

        vm.cleanup()

    def test_is_cgjson_file(self):
        """Test detecting CGJson files."""
        vm = FileIOViewModel()
        vm.initialize()

        # Reset state
        vm._store.update(file_path=None)
        vm.current_file_path = None

        # No file
        assert vm.is_cgjson_file() is False

        # CGJson file
        vm.set_current_file("/path/to/file.cgjson")
        assert vm.is_cgjson_file() is True

        # CGZ file
        vm.set_current_file("/path/to/file.cgz")
        assert vm.is_cgjson_file() is True

        # JSON file
        vm.set_current_file("/path/to/file.json")
        assert vm.is_cgjson_file() is True

        # Other file
        vm.set_current_file("/path/to/file.drawio")
        assert vm.is_cgjson_file() is False

        vm.cleanup()

    def test_recent_files(self):
        """Test recent files management."""
        vm = FileIOViewModel()
        vm.initialize()

        # Add files
        vm.set_current_file("/path/to/file1.drawio")
        vm.set_current_file("/path/to/file2.drawio")
        vm.set_current_file("/path/to/file3.drawio")

        recent = vm.get_recent_files()
        assert len(recent) == 3
        assert recent[0] == "/path/to/file3.drawio"  # Most recent first
        assert recent[1] == "/path/to/file2.drawio"
        assert recent[2] == "/path/to/file1.drawio"

        vm.cleanup()

    def test_recent_files_duplicates(self):
        """Test recent files handles duplicates."""
        vm = FileIOViewModel()
        vm.initialize()

        # Add same file twice
        vm.set_current_file("/path/to/file1.drawio")
        vm.set_current_file("/path/to/file2.drawio")
        vm.set_current_file("/path/to/file1.drawio")  # Duplicate

        recent = vm.get_recent_files()
        assert len(recent) == 2
        assert recent[0] == "/path/to/file1.drawio"  # Moved to front
        assert recent[1] == "/path/to/file2.drawio"

        vm.cleanup()

    def test_recent_files_max_limit(self):
        """Test recent files respects max limit."""
        vm = FileIOViewModel()
        vm.initialize()

        # Add more than MAX_RECENT_FILES
        for i in range(15):
            vm.set_current_file(f"/path/to/file{i}.drawio")

        recent = vm.get_recent_files()
        assert len(recent) == vm.MAX_RECENT_FILES
        assert recent[0] == "/path/to/file14.drawio"  # Most recent

        vm.cleanup()

    def test_clear_recent_files(self):
        """Test clearing recent files."""
        vm = FileIOViewModel()
        vm.initialize()

        vm.set_current_file("/path/to/file1.drawio")
        vm.set_current_file("/path/to/file2.drawio")
        
        vm.clear_recent_files()

        assert vm.get_recent_files() == []

        vm.cleanup()

    def test_window_title(self):
        """Test window title generation."""
        vm = FileIOViewModel()
        vm.initialize()

        # Reset state
        vm._store.update(file_path=None)
        vm.current_file_path = None
        vm.is_modified = False

        # No file
        assert vm.window_title == "Untitled"

        # With file, not modified
        vm.set_current_file("/path/to/my_graph.drawio")
        assert vm.window_title == "my_graph.drawio"

        # With file, modified
        vm.mark_as_modified(True)
        assert vm.window_title == "my_graph.drawio *"

        vm.cleanup()

    def test_can_save_property(self):
        """Test can_save property."""
        vm = FileIOViewModel()
        vm.initialize()

        # No file
        assert vm.can_save is False

        # With file, not modified
        vm.set_current_file("/path/to/file.drawio")
        assert vm.can_save is False

        # With file, modified
        vm.mark_as_modified(True)
        assert vm.can_save is True

        vm.cleanup()

    def test_event_publishing_on_open(self):
        """Test that opening a file publishes FILE_OPENED event."""
        vm = FileIOViewModel()
        vm.initialize()

        events = []
        vm._event_bus.subscribe(EventType.FILE_OPENED, lambda e: events.append(e))

        vm.on_file_opened("/path/to/file.drawio")

        assert len(events) == 2  # set_current_file + on_file_opened
        assert events[-1].type == EventType.FILE_OPENED
        assert events[-1].payload["file_path"] == "/path/to/file.drawio"

        vm.cleanup()

    def test_event_publishing_on_save(self):
        """Test that saving a file publishes FILE_SAVED event."""
        vm = FileIOViewModel()
        vm.initialize()

        events = []
        vm._event_bus.subscribe(EventType.FILE_SAVED, lambda e: events.append(e))

        vm.on_file_saved("/path/to/file.drawio")

        assert len(events) == 1
        assert events[0].type == EventType.FILE_SAVED
        assert events[0].payload["file_path"] == "/path/to/file.drawio"

        vm.cleanup()

    def test_event_publishing_on_new(self):
        """Test that new file publishes FILE_CLOSED event."""
        vm = FileIOViewModel()
        vm.initialize()

        events = []
        vm._event_bus.subscribe(EventType.FILE_CLOSED, lambda e: events.append(e))

        vm.on_file_new()

        assert len(events) == 1
        assert events[0].type == EventType.FILE_CLOSED

        vm.cleanup()

    def test_observable_properties(self):
        """Test observable properties trigger callbacks."""
        vm = FileIOViewModel()
        vm.initialize()

        # Test current_file_path observable
        observations = []
        vm.observe_property("current_file_path", lambda old, new: observations.append(new))

        vm.set_current_file("/path/to/file.drawio")

        assert len(observations) == 1
        assert observations[0] == "/path/to/file.drawio"

        vm.cleanup()

    def test_state_store_integration(self):
        """Test that file path is stored in state store."""
        vm = FileIOViewModel()
        vm.initialize()

        vm.set_current_file("/path/to/file.drawio")

        state = vm._store.get_state()
        assert state.file_path == "/path/to/file.drawio"

        vm.cleanup()
