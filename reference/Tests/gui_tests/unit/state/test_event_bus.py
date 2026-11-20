"""
Unit tests for event bus.

Tests the EventBus publish-subscribe implementation.
"""

import pytest

from gui_framework.events.bus import Event, EventBus, EventType, get_event_bus


class TestEvent:
    """Tests for Event dataclass."""

    def test_event_creation(self):
        """Test creating an event."""
        event = Event(
            type=EventType.NODE_CREATED,
            payload={"node_id": "node_123"},
            sender="CanvasViewModel",
        )

        assert event.type == EventType.NODE_CREATED
        assert event.payload["node_id"] == "node_123"
        assert event.sender == "CanvasViewModel"

    def test_event_minimal(self):
        """Test creating event with minimal arguments."""
        event = Event(type=EventType.NODE_CREATED)

        assert event.type == EventType.NODE_CREATED
        assert event.payload is None
        assert event.sender == ""


class TestEventBus:
    """Tests for EventBus class."""

    def test_bus_initialization(self):
        """Test that bus initializes correctly."""
        bus = EventBus()

        assert bus.get_queue_size() == 0
        assert bus.get_all_subscribers() == {}

    def test_subscribe(self):
        """Test subscribing to events."""
        bus = EventBus()
        called = []

        def callback(event):
            called.append(event)

        bus.subscribe(EventType.NODE_CREATED, callback)

        assert bus.get_subscriber_count(EventType.NODE_CREATED) == 1

    def test_subscribe_multiple_callbacks(self):
        """Test subscribing multiple callbacks to same event."""
        bus = EventBus()

        def callback1(event):
            pass

        def callback2(event):
            pass

        bus.subscribe(EventType.NODE_CREATED, callback1)
        bus.subscribe(EventType.NODE_CREATED, callback2)

        assert bus.get_subscriber_count(EventType.NODE_CREATED) == 2

    def test_subscribe_same_callback_twice(self):
        """Test that subscribing same callback twice only adds it once."""
        bus = EventBus()

        def callback(event):
            pass

        bus.subscribe(EventType.NODE_CREATED, callback)
        bus.subscribe(EventType.NODE_CREATED, callback)

        # Should only be subscribed once
        assert bus.get_subscriber_count(EventType.NODE_CREATED) == 1

    def test_publish_sync(self):
        """Test synchronous event publishing."""
        bus = EventBus()
        called = []

        def callback(event):
            called.append(event)

        bus.subscribe(EventType.NODE_CREATED, callback)

        event = Event(type=EventType.NODE_CREATED, payload={"test": "data"})
        bus.publish(event)

        assert len(called) == 1
        assert called[0].payload["test"] == "data"

    def test_publish_multiple_subscribers(self):
        """Test publishing to multiple subscribers."""
        bus = EventBus()
        called1 = []
        called2 = []

        def callback1(event):
            called1.append(event)

        def callback2(event):
            called2.append(event)

        bus.subscribe(EventType.NODE_CREATED, callback1)
        bus.subscribe(EventType.NODE_CREATED, callback2)

        event = Event(type=EventType.NODE_CREATED)
        bus.publish(event)

        assert len(called1) == 1
        assert len(called2) == 1

    def test_publish_no_subscribers(self):
        """Test publishing with no subscribers doesn't crash."""
        bus = EventBus()

        event = Event(type=EventType.NODE_CREATED)
        bus.publish(event)  # Should not raise

    def test_publish_wrong_event_type(self):
        """Test that wrong event type doesn't call subscriber."""
        bus = EventBus()
        called = []

        def callback(event):
            called.append(event)

        bus.subscribe(EventType.NODE_CREATED, callback)

        event = Event(type=EventType.NODE_DELETED)
        bus.publish(event)

        assert len(called) == 0

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        called = []

        def callback(event):
            called.append(event)

        bus.subscribe(EventType.NODE_CREATED, callback)
        bus.unsubscribe(EventType.NODE_CREATED, callback)

        assert bus.get_subscriber_count(EventType.NODE_CREATED) == 0

        event = Event(type=EventType.NODE_CREATED)
        bus.publish(event)

        assert len(called) == 0

    def test_unsubscribe_nonexistent(self):
        """Test unsubscribing nonexistent callback doesn't crash."""
        bus = EventBus()

        def callback(event):
            pass

        # Should not raise
        bus.unsubscribe(EventType.NODE_CREATED, callback)

    def test_unsubscribe_all(self):
        """Test unsubscribing all callbacks from event type."""
        bus = EventBus()

        def callback1(event):
            pass

        def callback2(event):
            pass

        bus.subscribe(EventType.NODE_CREATED, callback1)
        bus.subscribe(EventType.NODE_CREATED, callback2)

        assert bus.get_subscriber_count(EventType.NODE_CREATED) == 2

        bus.unsubscribe_all(EventType.NODE_CREATED)

        assert bus.get_subscriber_count(EventType.NODE_CREATED) == 0

    def test_publish_async(self):
        """Test asynchronous event publishing."""
        bus = EventBus()

        event = Event(type=EventType.NODE_CREATED)
        bus.publish_async(event)

        assert bus.get_queue_size() == 1

    def test_process_queue(self):
        """Test processing queued events."""
        bus = EventBus()
        called = []

        def callback(event):
            called.append(event)

        bus.subscribe(EventType.NODE_CREATED, callback)

        # Queue events
        bus.publish_async(Event(type=EventType.NODE_CREATED))
        bus.publish_async(Event(type=EventType.NODE_CREATED))

        assert bus.get_queue_size() == 2
        assert len(called) == 0

        # Process queue
        processed = bus.process_queue()

        assert processed == 2
        assert bus.get_queue_size() == 0
        assert len(called) == 2

    def test_clear_queue(self):
        """Test clearing event queue."""
        bus = EventBus()

        bus.publish_async(Event(type=EventType.NODE_CREATED))
        bus.publish_async(Event(type=EventType.NODE_CREATED))

        assert bus.get_queue_size() == 2

        bus.clear_queue()

        assert bus.get_queue_size() == 0

    def test_get_all_subscribers(self):
        """Test getting all subscriber counts."""
        bus = EventBus()

        def callback(event):
            pass

        bus.subscribe(EventType.NODE_CREATED, callback)
        bus.subscribe(EventType.NODE_DELETED, callback)

        subscribers = bus.get_all_subscribers()

        assert subscribers[EventType.NODE_CREATED] == 1
        assert subscribers[EventType.NODE_DELETED] == 1

    def test_callback_error_handling(self):
        """Test that callback errors don't crash the bus."""
        bus = EventBus()
        called = []

        def bad_callback(event):
            raise ValueError("Test error")

        def good_callback(event):
            called.append(event)

        bus.subscribe(EventType.NODE_CREATED, bad_callback)
        bus.subscribe(EventType.NODE_CREATED, good_callback)

        # Should not raise, error should be caught
        event = Event(type=EventType.NODE_CREATED)
        bus.publish(event)

        # Good callback should still be called
        assert len(called) == 1

    def test_callback_order(self):
        """Test that callbacks are called in subscription order."""
        bus = EventBus()
        call_order = []

        def callback1(event):
            call_order.append(1)

        def callback2(event):
            call_order.append(2)

        def callback3(event):
            call_order.append(3)

        bus.subscribe(EventType.NODE_CREATED, callback1)
        bus.subscribe(EventType.NODE_CREATED, callback2)
        bus.subscribe(EventType.NODE_CREATED, callback3)

        event = Event(type=EventType.NODE_CREATED)
        bus.publish(event)

        assert call_order == [1, 2, 3]


class TestGetEventBus:
    """Tests for get_event_bus singleton."""

    def test_get_event_bus_returns_instance(self):
        """Test that get_event_bus returns an EventBus instance."""
        bus = get_event_bus()
        assert isinstance(bus, EventBus)

    def test_get_event_bus_returns_same_instance(self):
        """Test that get_event_bus returns the same singleton."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_singleton_persists_subscriptions(self):
        """Test that singleton persists subscriptions across calls."""
        bus1 = get_event_bus()

        def callback(event):
            pass

        bus1.subscribe(EventType.NODE_CREATED, callback)

        bus2 = get_event_bus()
        assert bus2.get_subscriber_count(EventType.NODE_CREATED) == 1


class TestEventTypes:
    """Tests for EventType enum."""

    def test_event_types_exist(self):
        """Test that expected event types exist."""
        assert EventType.NODE_CREATED
        assert EventType.NODE_DELETED
        assert EventType.EDGE_CREATED
        assert EventType.EXECUTION_STARTED
        assert EventType.GRAPH_LOADED
        assert EventType.THEME_UPDATED

    def test_event_type_values(self):
        """Test that event type values are strings."""
        assert isinstance(EventType.NODE_CREATED.value, str)
        assert EventType.NODE_CREATED.value == "node_created"
