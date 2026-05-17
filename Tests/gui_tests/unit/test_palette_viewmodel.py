"""
Tests for PaletteViewModel

Tests palette state management, node loading, search/filter, and category expansion.
"""

import pytest
from gui_framework.viewmodels.palette_viewmodel import PaletteViewModel, NodeInfo
from gui_framework.state.store import StateStore
from gui_framework.state.models import AppState, PaletteState
from gui_framework.events.bus import EventBus


class TestPaletteViewModelInitialization:
    """Test PaletteViewModel initialization and setup."""
    
    def test_initialization(self):
        """Test basic initialization."""
        vm = PaletteViewModel()
        vm.initialize()
        
        # Should have loaded categories
        assert vm.get_category_count() >= 0
        assert vm.get_total_node_count() >= 0
        
        # Default state
        assert vm.search_text == ""
        
        vm.cleanup()
    
    def test_categories_loaded(self):
        """Test that categories are loaded from registry."""
        vm = PaletteViewModel()
        vm.initialize()
        
        categories = vm.categories
        assert isinstance(categories, dict)
        
        # Should have some basic categories (may vary based on registry)
        # Just verify structure
        for category_name, nodes in categories.items():
            assert isinstance(category_name, str)
            assert isinstance(nodes, list)
            for node in nodes:
                assert isinstance(node, NodeInfo)
                assert hasattr(node, 'node_type')
                assert hasattr(node, 'display_name')
                assert hasattr(node, 'description')
                assert hasattr(node, 'category')
        
        vm.cleanup()
    
    def test_expanded_categories_default(self):
        """Test that all categories are expanded by default."""
        vm = PaletteViewModel()
        vm.initialize()
        
        expanded = vm.expanded_categories
        categories = vm.categories
        
        # All categories should be expanded by default
        for category_name in categories.keys():
            assert category_name in expanded
        
        vm.cleanup()


class TestPaletteViewModelSearch:
    """Test search and filter functionality."""
    
    def test_search_text_property(self):
        """Test search_text property."""
        vm = PaletteViewModel()
        vm.initialize()
        
        assert vm.search_text == ""
        
        vm.set_search_text("Addition")
        assert vm.search_text == "Addition"
        
        vm.cleanup()
    
    def test_search_filters_nodes(self):
        """Test that search filters nodes correctly."""
        vm = PaletteViewModel()
        vm.initialize()
        
        # No filter: all nodes
        all_nodes = vm.filtered_nodes
        total_count = len(all_nodes)
        
        # Apply filter
        vm.set_search_text("Add")
        filtered = vm.filtered_nodes
        
        # Should have fewer (or equal) nodes
        assert len(filtered) <= total_count
        
        # All filtered nodes should match search
        for node in filtered:
            search_text = "add"  # lowercase for comparison
            assert (
                search_text in node.display_name.lower() or
                search_text in node.node_type.lower() or
                search_text in node.description.lower() or
                search_text in node.category.lower()
            )
        
        vm.cleanup()
    
    def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        vm = PaletteViewModel()
        vm.initialize()
        
        vm.set_search_text("ADDITION")
        filtered_upper = vm.filtered_nodes
        
        vm.set_search_text("addition")
        filtered_lower = vm.filtered_nodes
        
        # Should return same results regardless of case
        assert len(filtered_upper) == len(filtered_lower)
        
        vm.cleanup()
    
    def test_clear_search(self):
        """Test clearing search text."""
        vm = PaletteViewModel()
        vm.initialize()
        
        vm.set_search_text("test")
        assert len(vm.filtered_nodes) <= vm.get_total_node_count()
        
        vm.set_search_text("")
        assert len(vm.filtered_nodes) == vm.get_total_node_count()
        
        vm.cleanup()
    
    def test_search_observer(self):
        """Test that search text changes notify observers."""
        vm = PaletteViewModel()
        vm.initialize()
        
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        vm.add_search_text_observer(callback)
        vm.set_search_text("test")
        
        assert len(callback_called) == 1
        
        vm.cleanup()


class TestPaletteViewModelCategories:
    """Test category expansion/collapse functionality."""
    
    def test_toggle_category(self):
        """Test toggling category expansion."""
        vm = PaletteViewModel()
        vm.initialize()
        
        categories = list(vm.categories.keys())
        if not categories:
            pytest.skip("No categories available")
        
        category = categories[0]
        
        # Initially expanded
        assert vm.is_category_expanded(category)
        
        # Toggle to collapse
        vm.toggle_category(category)
        assert not vm.is_category_expanded(category)
        
        # Toggle to expand
        vm.toggle_category(category)
        assert vm.is_category_expanded(category)
        
        vm.cleanup()
    
    def test_expand_category(self):
        """Test expanding a specific category."""
        vm = PaletteViewModel()
        vm.initialize()
        
        categories = list(vm.categories.keys())
        if not categories:
            pytest.skip("No categories available")
        
        category = categories[0]
        
        # Collapse first
        vm.collapse_category(category)
        assert not vm.is_category_expanded(category)
        
        # Expand
        vm.expand_category(category)
        assert vm.is_category_expanded(category)
        
        vm.cleanup()
    
    def test_collapse_category(self):
        """Test collapsing a specific category."""
        vm = PaletteViewModel()
        vm.initialize()
        
        categories = list(vm.categories.keys())
        if not categories:
            pytest.skip("No categories available")
        
        category = categories[0]
        
        # Ensure expanded first
        vm.expand_category(category)
        assert vm.is_category_expanded(category)
        
        # Collapse
        vm.collapse_category(category)
        assert not vm.is_category_expanded(category)
        
        vm.cleanup()
    
    def test_expand_all_categories(self):
        """Test expanding all categories."""
        vm = PaletteViewModel()
        vm.initialize()
        
        # Collapse all first
        vm.collapse_all_categories()
        
        # Expand all
        vm.expand_all_categories()
        
        categories = vm.categories
        for category_name in categories.keys():
            assert vm.is_category_expanded(category_name)
        
        vm.cleanup()
    
    def test_collapse_all_categories(self):
        """Test collapsing all categories."""
        vm = PaletteViewModel()
        vm.initialize()
        
        # Expand all first
        vm.expand_all_categories()
        
        # Collapse all
        vm.collapse_all_categories()
        
        categories = vm.categories
        for category_name in categories.keys():
            assert not vm.is_category_expanded(category_name)
        
        vm.cleanup()
    
    def test_category_observer(self):
        """Test that category changes notify observers."""
        vm = PaletteViewModel()
        vm.initialize()
        
        categories = list(vm.categories.keys())
        if not categories:
            pytest.skip("No categories available")
        
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        vm.add_expanded_categories_observer(callback)
        vm.toggle_category(categories[0])
        
        assert len(callback_called) == 1
        
        vm.cleanup()


class TestPaletteViewModelNodeInfo:
    """Test node information retrieval."""
    
    def test_get_nodes_in_category(self):
        """Test retrieving nodes in a specific category."""
        vm = PaletteViewModel()
        vm.initialize()
        
        categories = vm.categories
        if not categories:
            pytest.skip("No categories available")
        
        category_name = list(categories.keys())[0]
        nodes = vm.get_nodes_in_category(category_name)
        
        assert isinstance(nodes, list)
        for node in nodes:
            assert isinstance(node, NodeInfo)
            assert node.category == category_name
        
        vm.cleanup()
    
    def test_get_node_info(self):
        """Test retrieving info for a specific node type."""
        vm = PaletteViewModel()
        vm.initialize()
        
        # Get first available node type
        all_types = vm.get_all_node_types()
        if not all_types:
            pytest.skip("No nodes available")
        
        node_type = all_types[0]
        node_info = vm.get_node_info(node_type)
        
        assert node_info is not None
        assert isinstance(node_info, NodeInfo)
        assert node_info.node_type == node_type
        
        vm.cleanup()
    
    def test_get_node_info_not_found(self):
        """Test retrieving info for non-existent node."""
        vm = PaletteViewModel()
        vm.initialize()
        
        node_info = vm.get_node_info("NonExistentNode")
        assert node_info is None
        
        vm.cleanup()
    
    def test_get_all_node_types(self):
        """Test retrieving all node types."""
        vm = PaletteViewModel()
        vm.initialize()
        
        node_types = vm.get_all_node_types()
        
        assert isinstance(node_types, list)
        for node_type in node_types:
            assert isinstance(node_type, str)
        
        # Should match total node count
        assert len(node_types) == vm.get_total_node_count()
        
        vm.cleanup()
    
    def test_get_category_count(self):
        """Test getting category count."""
        vm = PaletteViewModel()
        vm.initialize()
        
        count = vm.get_category_count()
        assert isinstance(count, int)
        assert count >= 0
        assert count == len(vm.categories)
        
        vm.cleanup()
    
    def test_get_total_node_count(self):
        """Test getting total node count."""
        vm = PaletteViewModel()
        vm.initialize()
        
        count = vm.get_total_node_count()
        assert isinstance(count, int)
        assert count >= 0
        
        # Verify by summing category nodes
        total = sum(len(nodes) for nodes in vm.categories.values())
        assert count == total
        
        vm.cleanup()


class TestPaletteViewModelStateStore:
    """Test StateStore integration."""
    
    def test_state_persistence(self):
        """Test that palette state is saved to StateStore."""
        store = StateStore()
        bus = EventBus()
        
        vm = PaletteViewModel()
        vm._store = store
        vm._bus = bus
        vm.initialize()
        
        # Change state
        vm.set_search_text("test search")
        
        categories = list(vm.categories.keys())
        if categories:
            vm.collapse_category(categories[0])
        
        # State should be saved
        state = store.get_state()
        assert hasattr(state, 'palette')
        assert state.palette.search_text == "test search"
        
        vm.cleanup()
    
    def test_state_restoration(self):
        """Test that palette state is restored from StateStore."""
        store = StateStore()
        bus = EventBus()
        
        # Set up initial state
        palette_state = PaletteState(
            search_text="restored search",
            expanded_categories=["Category1", "Category2"]
        )
        store.update(palette=palette_state)
        
        # Create new VM with that state
        vm = PaletteViewModel()
        vm._store = store
        vm._bus = bus
        vm.initialize()
        
        # State should be restored
        assert vm.search_text == "restored search"
        assert "Category1" in vm.expanded_categories
        assert "Category2" in vm.expanded_categories
        
        vm.cleanup()


class TestPaletteViewModelEvents:
    """Test event bus integration."""
    
    def test_search_changed_event(self):
        """Test that search changes publish events."""
        store = StateStore()
        bus = EventBus()
        
        vm = PaletteViewModel()
        vm._store = store
        vm._event_bus = bus
        vm.initialize()
        
        events_received = []
        
        def handler(event):
            events_received.append(event)
        
        from gui_framework.events.bus import EventType
        bus.subscribe(EventType.CUSTOM, handler)
        
        vm.set_search_text("test")
        
        assert len(events_received) == 1
        # Check that it's our event
        event = events_received[0]
        assert event.payload['event_type'] == 'PALETTE_SEARCH_CHANGED'
        assert event.payload['text'] == "test"
        
        vm.cleanup()
    
    def test_category_toggled_event(self):
        """Test that category toggles publish events."""
        store = StateStore()
        bus = EventBus()
        
        vm = PaletteViewModel()
        vm._store = store
        vm._event_bus = bus
        vm.initialize()
        
        categories = list(vm.categories.keys())
        if not categories:
            pytest.skip("No categories available")
        
        events_received = []
        
        def handler(event):
            events_received.append(event)
        
        from gui_framework.events.bus import EventType
        bus.subscribe(EventType.CUSTOM, handler)
        
        vm.toggle_category(categories[0])
        
        assert len(events_received) == 1
        event = events_received[0]
        assert event.payload['event_type'] == 'PALETTE_CATEGORY_TOGGLED'
        assert event.payload['category'] == categories[0]
        assert 'expanded' in event.payload
        
        vm.cleanup()


class TestPaletteViewModelObservableProperties:
    """Test observable property behavior."""
    
    def test_categories_observable(self):
        """Test categories as observable property."""
        vm = PaletteViewModel()
        vm.initialize()
        
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        vm.add_categories_observer(callback)
        
        # Categories don't change after init, but property is observable
        categories = vm.categories
        assert isinstance(categories, dict)
        
        vm.cleanup()
    
    def test_filtered_nodes_observable(self):
        """Test filtered_nodes as observable property."""
        from gui_framework.state.store import StateStore
        from gui_framework.events.bus import EventBus
        
        store = StateStore()
        bus = EventBus()
        
        vm = PaletteViewModel()
        vm._store = store
        vm._event_bus = bus
        vm.initialize()
        
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        vm.add_filtered_nodes_observer(callback)
        
        # Changing search updates filtered nodes
        vm.set_search_text("test")
        
        assert len(callback_called) == 1
        
        vm.cleanup()
