"""
Unit tests for CollapsibleSection ViewModel.

Tests the CollapsibleSectionViewModel pure Python logic.
"""

import pytest

from gui_framework.widgets.collapsible_section_viewmodel import (
    CollapsibleSectionViewModel,
)


class TestCollapsibleSectionViewModel:
    """Tests for CollapsibleSectionViewModel."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        vm = CollapsibleSectionViewModel()

        assert vm.title == ""
        assert vm.is_expanded is True
        assert not vm.is_initialized()

    def test_initialization_with_parameters(self):
        """Test initialization with parameters."""
        vm = CollapsibleSectionViewModel(title="Settings", expanded=False)

        assert vm.title == "Settings"
        assert vm.is_expanded is False

    def test_initialize(self):
        """Test initialize method."""
        vm = CollapsibleSectionViewModel()

        # Should not raise
        vm.initialize()

        # Mark as initialized
        vm._mark_initialized()
        assert vm.is_initialized()

    def test_cleanup(self):
        """Test cleanup method."""
        vm = CollapsibleSectionViewModel()

        # Should not raise
        vm.cleanup()

    def test_toggle_from_expanded(self):
        """Test toggling from expanded state."""
        vm = CollapsibleSectionViewModel(expanded=True)

        assert vm.is_expanded is True
        vm.toggle()
        assert vm.is_expanded is False

    def test_toggle_from_collapsed(self):
        """Test toggling from collapsed state."""
        vm = CollapsibleSectionViewModel(expanded=False)

        assert vm.is_expanded is False
        vm.toggle()
        assert vm.is_expanded is True

    def test_multiple_toggles(self):
        """Test multiple consecutive toggles."""
        vm = CollapsibleSectionViewModel(expanded=True)

        vm.toggle()
        assert vm.is_expanded is False
        vm.toggle()
        assert vm.is_expanded is True
        vm.toggle()
        assert vm.is_expanded is False

    def test_expand(self):
        """Test explicit expand."""
        vm = CollapsibleSectionViewModel(expanded=False)

        vm.expand()
        assert vm.is_expanded is True

        # Expand again should be idempotent
        vm.expand()
        assert vm.is_expanded is True

    def test_collapse(self):
        """Test explicit collapse."""
        vm = CollapsibleSectionViewModel(expanded=True)

        vm.collapse()
        assert vm.is_expanded is False

        # Collapse again should be idempotent
        vm.collapse()
        assert vm.is_expanded is False

    def test_set_title(self):
        """Test changing the title."""
        vm = CollapsibleSectionViewModel(title="Original")

        assert vm.title == "Original"

        vm.set_title("New Title")
        assert vm.title == "New Title"

    def test_title_observable(self):
        """Test that title changes notify observers."""
        vm = CollapsibleSectionViewModel(title="Original")
        changes = []

        vm.observe_property("title", lambda old, new: changes.append((old, new)))

        vm.set_title("New Title")

        assert len(changes) == 1
        assert changes[0] == ("Original", "New Title")

    def test_is_expanded_observable(self):
        """Test that is_expanded changes notify observers."""
        vm = CollapsibleSectionViewModel(expanded=True)
        changes = []

        vm.observe_property("is_expanded", lambda old, new: changes.append((old, new)))

        vm.toggle()

        assert len(changes) == 1
        assert changes[0] == (True, False)

    def test_multiple_observers(self):
        """Test multiple observers for same property."""
        vm = CollapsibleSectionViewModel(expanded=True)
        changes1 = []
        changes2 = []

        vm.observe_property("is_expanded", lambda o, n: changes1.append((o, n)))
        vm.observe_property("is_expanded", lambda o, n: changes2.append((o, n)))

        vm.toggle()

        assert len(changes1) == 1
        assert len(changes2) == 1

    def test_unobserve(self):
        """Test unobserving properties."""
        vm = CollapsibleSectionViewModel()
        changes = []

        callback = lambda o, n: changes.append((o, n))
        vm.observe_property("is_expanded", callback)

        vm.toggle()
        assert len(changes) == 1

        vm.unobserve_property("is_expanded", callback)
        vm.toggle()

        # Should not be called again
        assert len(changes) == 1

    def test_direct_property_assignment(self):
        """Test direct property assignment notifies observers."""
        vm = CollapsibleSectionViewModel()
        changes = []

        vm.observe_property("is_expanded", lambda o, n: changes.append((o, n)))

        # Direct assignment should also trigger observers
        vm.is_expanded = False

        assert len(changes) == 1
        assert changes[0] == (True, False)

    def test_has_store_and_event_bus(self):
        """Test that ViewModel has access to store and event bus."""
        vm = CollapsibleSectionViewModel()

        assert vm._store is not None
        assert vm._event_bus is not None
