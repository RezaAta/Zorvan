"""
Unit tests for widget registry.

Tests WidgetRegistry plugin system.
"""

import pytest
from gui_framework.registry.widget_registry import WidgetRegistry, get_widget_registry
from gui_framework.viewmodels.base import BaseViewModel


# Mock classes for testing
class MockViewModel(BaseViewModel):
    def initialize(self):
        pass
    
    def cleanup(self):
        pass


class MockView:
    def __init__(self, viewmodel, parent=None):
        self.viewmodel = viewmodel
        self.parent = parent


class TestWidgetRegistry:
    """Tests for WidgetRegistry class."""
    
    def test_initialization(self):
        """Test registry initializes empty."""
        registry = WidgetRegistry()
        
        assert registry.get_registered_widgets() == []
    
    def test_register_widget(self):
        """Test registering a widget."""
        registry = WidgetRegistry()
        
        registry.register_widget(
            name="test_widget",
            viewmodel_cls=MockViewModel,
            view_cls=MockView
        )
        
        assert registry.is_registered("test_widget")
        assert "test_widget" in registry.get_registered_widgets()
    
    def test_register_duplicate_raises(self):
        """Test that registering duplicate name raises error."""
        registry = WidgetRegistry()
        
        registry.register_widget("test", MockViewModel, MockView)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register_widget("test", MockViewModel, MockView)
    
    def test_unregister_widget(self):
        """Test unregistering a widget."""
        registry = WidgetRegistry()
        
        registry.register_widget("test", MockViewModel, MockView)
        assert registry.is_registered("test")
        
        registry.unregister_widget("test")
        assert not registry.is_registered("test")
    
    def test_create_widget(self):
        """Test creating a widget instance."""
        registry = WidgetRegistry()
        registry.register_widget("test", MockViewModel, MockView)
        
        viewmodel, view = registry.create_widget("test")
        
        assert isinstance(viewmodel, MockViewModel)
        assert isinstance(view, MockView)
        assert view.viewmodel is viewmodel
    
    def test_create_unregistered_raises(self):
        """Test that creating unregistered widget raises error."""
        registry = WidgetRegistry()
        
        with pytest.raises(ValueError, match="not registered"):
            registry.create_widget("nonexistent")
    
    def test_register_with_metadata(self):
        """Test registering widget with metadata."""
        registry = WidgetRegistry()
        
        metadata = {
            "category": "examples",
            "description": "Test widget",
            "icon": "test.png"
        }
        
        registry.register_widget(
            "test",
            MockViewModel,
            MockView,
            metadata=metadata
        )
        
        retrieved = registry.get_widget_metadata("test")
        assert retrieved == metadata
    
    def test_get_metadata_empty(self):
        """Test getting metadata for widget without metadata."""
        registry = WidgetRegistry()
        registry.register_widget("test", MockViewModel, MockView)
        
        metadata = registry.get_widget_metadata("test")
        assert metadata == {}
    
    def test_get_widgets_by_category(self):
        """Test getting widgets by category."""
        registry = WidgetRegistry()
        
        registry.register_widget(
            "widget1",
            MockViewModel,
            MockView,
            metadata={"category": "cat1"}
        )
        registry.register_widget(
            "widget2",
            MockViewModel,
            MockView,
            metadata={"category": "cat1"}
        )
        registry.register_widget(
            "widget3",
            MockViewModel,
            MockView,
            metadata={"category": "cat2"}
        )
        
        cat1_widgets = registry.get_widgets_by_category("cat1")
        assert len(cat1_widgets) == 2
        assert "widget1" in cat1_widgets
        assert "widget2" in cat1_widgets
    
    def test_custom_factory(self):
        """Test registering widget with custom factory."""
        registry = WidgetRegistry()
        
        factory_called = []
        
        def custom_factory(**kwargs):
            factory_called.append(kwargs)
            vm = MockViewModel()
            view = MockView(vm)
            return vm, view
        
        registry.register_widget(
            "test",
            MockViewModel,
            MockView,
            factory=custom_factory
        )
        
        viewmodel, view = registry.create_widget("test", custom_arg="value")
        
        assert len(factory_called) == 1
        assert factory_called[0] == {"custom_arg": "value"}


class TestGetWidgetRegistry:
    """Tests for get_widget_registry singleton."""
    
    def test_returns_instance(self):
        """Test that get_widget_registry returns an instance."""
        registry = get_widget_registry()
        assert isinstance(registry, WidgetRegistry)
    
    def test_returns_same_instance(self):
        """Test that get_widget_registry returns the same singleton."""
        registry1 = get_widget_registry()
        registry2 = get_widget_registry()
        assert registry1 is registry2
    
    def test_singleton_persists_registrations(self):
        """Test that singleton persists registrations."""
        registry1 = get_widget_registry()
        registry1.register_widget("test", MockViewModel, MockView)
        
        registry2 = get_widget_registry()
        assert registry2.is_registered("test")
