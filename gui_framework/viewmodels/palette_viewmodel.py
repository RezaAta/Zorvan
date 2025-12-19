"""
PaletteViewModel - ViewModel for Node Palette

Manages node palette state including categories, search/filter, and node selection.
Integrates with node_registry.py for node definitions and StateStore for persistence.
"""

from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from gui_framework.viewmodels.base import BaseViewModel
from gui_framework.state.models import PaletteState
from gui_framework.events.bus import Event, EventType


@dataclass
class NodeInfo:
    """Information about a node available in the palette."""
    node_type: str
    display_name: str
    description: str
    category: str


class PaletteViewModel(BaseViewModel):
    """ViewModel for managing node palette state and operations.
    
    Responsibilities:
    - Load and manage node categories from registry
    - Handle search/filter operations
    - Track expanded/collapsed categories
    - Provide node information for UI rendering
    - Integrate with StateStore for persistence
    
    Observable Properties:
    - categories: Dict of category name -> list of NodeInfo
    - search_text: Current search/filter text
    - expanded_categories: Set of expanded category names
    - filtered_nodes: List of NodeInfo matching current filter
    """
    
    def __init__(self):
        super().__init__()
        self._categories: Dict[str, List[NodeInfo]] = {}
        self._all_nodes: List[NodeInfo] = []
        self._search_text: str = ""
        self._expanded_categories: set = set()
        self._filtered_nodes: List[NodeInfo] = []
        # Observers for properties (callback list per property name)
        self._observers: Dict[str, List[Callable]] = {}
        
    def initialize(self) -> None:
        """Initialize the ViewModel and load node categories."""
        self._load_categories()
        
        # Load state from StateStore if available
        try:
            state = self._store.get_state()
            if hasattr(state, 'palette'):
                palette_state = state.palette
                self._search_text = palette_state.search_text
                self._expanded_categories = set(palette_state.expanded_categories)
        except Exception:
            # Expand all categories by default
            self._expanded_categories = set(self._categories.keys())
        
        self._update_filtered_nodes()
        self._mark_initialized()
        
    def _load_categories(self) -> None:
        """Load node categories from node_registry."""
        try:
            # Import node_registry from GUI package
            import sys
            import os
            # Get absolute path to repository root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
            if repo_root not in sys.path:
                sys.path.insert(0, repo_root)
            
            from ComputationalGraphs.GUI.node_registry import get_node_categories
            
            categories_data = get_node_categories()
            
            # Convert to NodeInfo objects
            for category_name, category_data in categories_data.items():
                nodes = []
                for node_tuple in category_data.get("nodes", []):
                    if len(node_tuple) >= 3:
                        node_type, display_name, description = node_tuple[:3]
                        node_info = NodeInfo(
                            node_type=node_type,
                            display_name=display_name,
                            description=description,
                            category=category_name
                        )
                        nodes.append(node_info)
                        self._all_nodes.append(node_info)
                
                if nodes:
                    self._categories[category_name] = nodes
                    
        except Exception as e:
            # Fallback: create empty categories
            print(f"Warning: Could not load node categories: {e}")
            self._categories = {}
            self._all_nodes = []
    
    def _add_observer(self, property_name: str, callback: Callable) -> None:
        """Add observer for a property."""
        if property_name not in self._observers:
            self._observers[property_name] = []
        if callback not in self._observers[property_name]:
            self._observers[property_name].append(callback)
    
    def _notify_observers(self, property_name: str) -> None:
        """Notify all observers of a property change."""
        if property_name in self._observers:
            for callback in self._observers[property_name][:]:
                try:
                    callback()
                except Exception as e:
                    print(f"Error in observer for {property_name}: {e}")
    
    def _publish_event(self, event_type_str: str, data: dict) -> None:
        """Publish an event to the event bus."""
        try:
            # Use CUSTOM event type with payload containing the event type string
            event = Event(
                type=EventType.CUSTOM,
                payload={'event_type': event_type_str, **data},
                sender="PaletteViewModel"
            )
            self._event_bus.publish(event)
        except Exception as e:
            print(f"Error publishing event {event_type_str}: {e}")
    
    # Observable property: categories
    @property
    def categories(self) -> Dict[str, List[NodeInfo]]:
        """Get all node categories."""
        return self._categories.copy()
    
    def add_categories_observer(self, callback: Callable) -> None:
        """Add observer for categories changes."""
        self._add_observer('categories', callback)
    
    # Observable property: search_text
    @property
    def search_text(self) -> str:
        """Get current search text."""
        return self._search_text
    
    def add_search_text_observer(self, callback: Callable) -> None:
        """Add observer for search text changes."""
        self._add_observer('search_text', callback)
    
    # Observable property: expanded_categories
    @property
    def expanded_categories(self) -> set:
        """Get set of expanded category names."""
        return self._expanded_categories.copy()
    
    def add_expanded_categories_observer(self, callback: Callable) -> None:
        """Add observer for expanded categories changes."""
        self._add_observer('expanded_categories', callback)
    
    # Observable property: filtered_nodes
    @property
    def filtered_nodes(self) -> List[NodeInfo]:
        """Get list of nodes matching current filter."""
        return self._filtered_nodes.copy()
    
    def add_filtered_nodes_observer(self, callback: Callable) -> None:
        """Add observer for filtered nodes changes."""
        self._add_observer('filtered_nodes', callback)
    
    # Operations
    def set_search_text(self, text: str) -> None:
        """Set search/filter text and update filtered nodes."""
        if self._search_text != text:
            self._search_text = text
            self._update_filtered_nodes()
            self._save_state()
            self._notify_observers('search_text')
            self._notify_observers('filtered_nodes')
            
            # Publish event
            self._publish_event('PALETTE_SEARCH_CHANGED', {'text': text})
    
    def toggle_category(self, category_name: str) -> None:
        """Toggle expanded/collapsed state of a category."""
        if category_name in self._categories:
            if category_name in self._expanded_categories:
                self._expanded_categories.remove(category_name)
            else:
                self._expanded_categories.add(category_name)
            
            self._save_state()
            self._notify_observers('expanded_categories')
            
            # Publish event
            self._publish_event('PALETTE_CATEGORY_TOGGLED', {
                'category': category_name,
                'expanded': category_name in self._expanded_categories
            })
    
    def expand_category(self, category_name: str) -> None:
        """Expand a category."""
        if category_name in self._categories and category_name not in self._expanded_categories:
            self._expanded_categories.add(category_name)
            self._save_state()
            self._notify_observers('expanded_categories')
    
    def collapse_category(self, category_name: str) -> None:
        """Collapse a category."""
        if category_name in self._expanded_categories:
            self._expanded_categories.remove(category_name)
            self._save_state()
            self._notify_observers('expanded_categories')
    
    def expand_all_categories(self) -> None:
        """Expand all categories."""
        self._expanded_categories = set(self._categories.keys())
        self._save_state()
        self._notify_observers('expanded_categories')
    
    def collapse_all_categories(self) -> None:
        """Collapse all categories."""
        self._expanded_categories.clear()
        self._save_state()
        self._notify_observers('expanded_categories')
    
    def get_nodes_in_category(self, category_name: str) -> List[NodeInfo]:
        """Get all nodes in a specific category."""
        return self._categories.get(category_name, []).copy()
    
    def get_node_info(self, node_type: str) -> Optional[NodeInfo]:
        """Get NodeInfo for a specific node type."""
        for node in self._all_nodes:
            if node.node_type == node_type:
                return node
        return None
    
    def get_all_node_types(self) -> List[str]:
        """Get list of all available node types."""
        return [node.node_type for node in self._all_nodes]
    
    def get_category_count(self) -> int:
        """Get number of categories."""
        return len(self._categories)
    
    def get_total_node_count(self) -> int:
        """Get total number of nodes across all categories."""
        return len(self._all_nodes)
    
    def is_category_expanded(self, category_name: str) -> bool:
        """Check if a category is expanded."""
        return category_name in self._expanded_categories
    
    def _update_filtered_nodes(self) -> None:
        """Update filtered nodes based on current search text."""
        if not self._search_text:
            # No filter: include all nodes
            self._filtered_nodes = self._all_nodes.copy()
        else:
            # Filter by search text (case-insensitive)
            search_lower = self._search_text.lower()
            self._filtered_nodes = [
                node for node in self._all_nodes
                if (search_lower in node.display_name.lower() or
                    search_lower in node.node_type.lower() or
                    search_lower in node.description.lower() or
                    search_lower in node.category.lower())
            ]
    
    def _save_state(self) -> None:
        """Save current palette state to StateStore."""
        try:
            palette_state = PaletteState(
                search_text=self._search_text,
                expanded_categories=list(self._expanded_categories)
            )
            self._store.update(palette=palette_state)
        except Exception as e:
            print(f"Warning: Could not save palette state: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self._save_state()
        super().cleanup()
