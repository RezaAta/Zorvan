"""
Event bus module.

Provides a publish-subscribe event system for loose coupling between components.
"""

from .bus import Event, EventBus, EventType, get_event_bus

__all__ = ["Event", "EventBus", "EventType", "get_event_bus"]
