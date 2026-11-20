"""
Unit tests for base ViewModel.

Tests BaseViewModel and ObservableProperty implementation.
"""

import pytest

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class ConcreteViewModel(BaseViewModel):
    """Concrete implementation for testing."""

    count = ObservableProperty("count", default=0)
    name = ObservableProperty("name", default="")

    def initialize(self):
        """Test initialization."""
        pass

    def cleanup(self):
        """Test cleanup."""
        pass


class TestObservableProperty:
    """Tests for ObservableProperty descriptor."""

    def test_default_value(self):
        """Test that default value is returned."""
        vm = ConcreteViewModel()
        assert vm.count == 0
        assert vm.name == ""

    def test_set_value(self):
        """Test setting property value."""
        vm = ConcreteViewModel()
        vm.count = 42
        assert vm.count == 42

    def test_property_change_notifies_observers(self):
        """Test that property changes notify observers."""
        vm = ConcreteViewModel()
        changes = []

        def observer(old, new):
            changes.append((old, new))

        vm.observe_property("count", observer)
        vm.count = 10

        assert len(changes) == 1
        assert changes[0] == (0, 10)

    def test_multiple_changes(self):
        """Test multiple property changes."""
        vm = ConcreteViewModel()
        changes = []

        vm.observe_property("count", lambda old, new: changes.append((old, new)))

        vm.count = 1
        vm.count = 2
        vm.count = 3

        assert len(changes) == 3
        assert changes == [(0, 1), (1, 2), (2, 3)]


class TestBaseViewModel:
    """Tests for BaseViewModel class."""

    def test_initialization(self):
        """Test viewmodel initialization."""
        vm = ConcreteViewModel()

        assert vm._store is not None
        assert vm._event_bus is not None
        assert vm._property_observers == {}
        assert vm._initialized is False

    def test_observe_property(self):
        """Test observing properties."""
        vm = ConcreteViewModel()
        called = []

        def callback(old, new):
            called.append((old, new))

        vm.observe_property("count", callback)
        vm.count = 5

        assert len(called) == 1
        assert called[0] == (0, 5)

    def test_observe_same_property_twice(self):
        """Test observing same property with same callback twice."""
        vm = ConcreteViewModel()
        called = []

        def callback(old, new):
            called.append((old, new))

        vm.observe_property("count", callback)
        vm.observe_property("count", callback)  # Should not add twice

        vm.count = 5

        # Should only be called once
        assert len(called) == 1

    def test_multiple_observers(self):
        """Test multiple observers for same property."""
        vm = ConcreteViewModel()
        called1 = []
        called2 = []

        vm.observe_property("count", lambda o, n: called1.append((o, n)))
        vm.observe_property("count", lambda o, n: called2.append((o, n)))

        vm.count = 5

        assert len(called1) == 1
        assert len(called2) == 1

    def test_unobserve_property(self):
        """Test unobserving properties."""
        vm = ConcreteViewModel()
        called = []

        def callback(old, new):
            called.append((old, new))

        vm.observe_property("count", callback)
        vm.count = 5
        assert len(called) == 1

        vm.unobserve_property("count", callback)
        vm.count = 10

        # Should not be called again
        assert len(called) == 1

    def test_observer_error_handling(self):
        """Test that observer errors don't crash the viewmodel."""
        vm = ConcreteViewModel()
        called = []

        def bad_observer(old, new):
            raise ValueError("Test error")

        def good_observer(old, new):
            called.append((old, new))

        vm.observe_property("count", bad_observer)
        vm.observe_property("count", good_observer)

        # Should not raise
        vm.count = 5

        # Good observer should still be called
        assert len(called) == 1

    def test_is_initialized(self):
        """Test initialization tracking."""
        vm = ConcreteViewModel()

        assert vm.is_initialized() is False

        vm._mark_initialized()

        assert vm.is_initialized() is True

    def test_multiple_properties(self):
        """Test multiple observable properties."""
        vm = ConcreteViewModel()
        count_changes = []
        name_changes = []

        vm.observe_property("count", lambda o, n: count_changes.append((o, n)))
        vm.observe_property("name", lambda o, n: name_changes.append((o, n)))

        vm.count = 10
        vm.name = "test"

        assert len(count_changes) == 1
        assert len(name_changes) == 1
        assert count_changes[0] == (0, 10)
        assert name_changes[0] == ("", "test")

    def test_abstract_methods_required(self):
        """Test that abstract methods must be implemented."""
        with pytest.raises(TypeError):
            # Should not be able to instantiate BaseViewModel directly
            BaseViewModel()
