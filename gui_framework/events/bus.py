"""
Event bus for loose coupling between components.

Provides a publish-subscribe pattern for system-wide events,
enabling components to communicate without direct dependencies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List
from threading import RLock


class EventType(Enum):
    """System-wide event types."""
    
    # UI Events - Node operations
    NODE_CREATED = "node_created"
    NODE_DELETED = "node_deleted"
    NODE_UPDATED = "node_updated"
    NODE_SELECTED = "node_selected"
    NODE_DESELECTED = "node_deselected"
    NODE_MOVED = "node_moved"
    
    # UI Events - Edge operations
    EDGE_CREATED = "edge_created"
    EDGE_DELETED = "edge_deleted"
    EDGE_SELECTED = "edge_selected"
    
    # Execution Events
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PAUSED = "execution_paused"
    EXECUTION_STOPPED = "execution_stopped"
    EXECUTION_STEP_COMPLETE = "execution_step_complete"
    EXECUTION_SPEED_CHANGED = "execution_speed_changed"
    EXECUTION_ERROR = "execution_error"
    
    # Graph Events
    GRAPH_LOADED = "graph_loaded"
    GRAPH_SAVED = "graph_saved"
    GRAPH_RESET = "graph_reset"
    GRAPH_MODIFIED = "graph_modified"
    
    # Canvas Events
    CANVAS_ZOOM_CHANGED = "canvas_zoom_changed"
    CANVAS_PAN_CHANGED = "canvas_pan_changed"
    CANVAS_SELECTION_CHANGED = "canvas_selection_changed"
    
    # Theme Events
    THEME_UPDATED = "theme_updated"
    THEME_COLOR_CHANGED = "theme_color_changed"
    THEME_FONT_CHANGED = "theme_font_changed"
    
    # File Events
    FILE_OPENED = "file_opened"
    FILE_SAVED = "file_saved"
    FILE_CLOSED = "file_closed"
    
    # Layout Events
    LAYOUT_APPLIED = "layout_applied"
    LAYOUT_CHANGED = "layout_changed"
    
    # Visualization Events
    VISUALIZATION_ENABLED = "visualization_enabled"
    VISUALIZATION_DISABLED = "visualization_disabled"
    
    # Custom/Generic Events
    CUSTOM = "custom"


@dataclass
class Event:
    """
    Event with payload.
    
    Attributes:
        type: The event type
        payload: Optional data associated with the event
        sender: Optional identifier of the event sender
    
    Example:
        >>> event = Event(
        ...     type=EventType.NODE_CREATED,
        ...     payload={"node_id": "node_123", "node_type": "AdditionNode"},
        ...     sender="CanvasViewModel"
        ... )
    """
    type: EventType
    payload: Any = None
    sender: str = ""


class EventBus:
    """
    Global event bus for loose coupling between components.
    
    Provides publish-subscribe pattern for system-wide events.
    Supports both synchronous and asynchronous event handling.
    
    Thread-safe for use from multiple threads (e.g., GUI and worker threads).
    
    Example:
        >>> bus = get_event_bus()
        >>> 
        >>> # Subscribe to events
        >>> def on_node_created(event):
        ...     print(f"Node created: {event.payload['node_id']}")
        >>> 
        >>> bus.subscribe(EventType.NODE_CREATED, on_node_created)
        >>> 
        >>> # Publish event
        >>> bus.publish(Event(
        ...     type=EventType.NODE_CREATED,
        ...     payload={"node_id": "node_123"}
        ... ))
    """
    
    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._event_queue: List[Event] = []
        self._lock = RLock()  # Thread-safe access
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type.
        
        The callback will be invoked whenever an event of the specified type
        is published.
        
        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when event is published.
                     Receives Event object as argument.
        
        Example:
            >>> def on_node_created(event):
            ...     node_id = event.payload["node_id"]
            ...     print(f"Node {node_id} was created")
            >>> 
            >>> bus.subscribe(EventType.NODE_CREATED, on_node_created)
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
        """
        with self._lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def unsubscribe_all(self, event_type: EventType) -> None:
        """
        Unsubscribe all callbacks from an event type.
        
        Args:
            event_type: The type of event to clear all subscribers from
        """
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type].clear()
    
    def publish(self, event: Event) -> None:
        """
        Publish an event synchronously.
        
        All subscribers for this event type will be notified immediately.
        Callbacks are invoked in the order they were subscribed.
        
        Args:
            event: The event to publish
        
        Example:
            >>> bus.publish(Event(
            ...     type=EventType.NODE_CREATED,
            ...     payload={"node_id": "node_123"},
            ...     sender="CanvasViewModel"
            ... ))
        """
        with self._lock:
            if event.type in self._subscribers:
                # Copy list to avoid modification during iteration
                subscribers = self._subscribers[event.type][:]
            else:
                subscribers = []
        
        # Call subscribers outside lock to avoid deadlock
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                # Log error but don't crash
                print(f"Error in event subscriber callback for {event.type}: {e}")
    
    def publish_async(self, event: Event) -> None:
        """
        Queue an event for asynchronous processing.
        
        The event is added to a queue and will be processed later when
        process_queue() is called (typically from the main event loop).
        
        This is useful for publishing events from worker threads without
        blocking them.
        
        Args:
            event: The event to queue
        
        Example:
            >>> # From worker thread
            >>> bus.publish_async(Event(
            ...     type=EventType.EXECUTION_STEP_COMPLETE,
            ...     payload={"iteration": 42}
            ... ))
            >>> 
            >>> # From main loop
            >>> bus.process_queue()
        """
        with self._lock:
            self._event_queue.append(event)
    
    def process_queue(self) -> int:
        """
        Process all queued events.
        
        This should be called periodically from the main event loop
        to process events that were queued via publish_async().
        
        Returns:
            Number of events processed
        
        Example:
            >>> # In main GUI loop
            >>> events_processed = bus.process_queue()
        """
        with self._lock:
            events_to_process = self._event_queue[:]
            self._event_queue.clear()
        
        for event in events_to_process:
            self.publish(event)
        
        return len(events_to_process)
    
    def get_queue_size(self) -> int:
        """
        Get the number of events in the queue.
        
        Returns:
            Number of queued events
        """
        with self._lock:
            return len(self._event_queue)
    
    def clear_queue(self) -> None:
        """Clear all queued events without processing them."""
        with self._lock:
            self._event_queue.clear()
    
    def get_subscriber_count(self, event_type: EventType) -> int:
        """
        Get the number of subscribers for an event type.
        
        Args:
            event_type: The event type to check
        
        Returns:
            Number of subscribers
        """
        with self._lock:
            return len(self._subscribers.get(event_type, []))
    
    def get_all_subscribers(self) -> Dict[EventType, int]:
        """
        Get subscriber counts for all event types.
        
        Returns:
            Dictionary mapping event types to subscriber counts
        """
        with self._lock:
            return {
                event_type: len(subscribers)
                for event_type, subscribers in self._subscribers.items()
            }


# Singleton instance
_bus: EventBus = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus singleton.
    
    Returns:
        The global EventBus instance
    
    Example:
        >>> bus = get_event_bus()
        >>> bus.subscribe(EventType.NODE_CREATED, my_callback)
    """
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
