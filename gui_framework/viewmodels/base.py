"""
Base ViewModel class and observable property pattern.

ViewModels contain all UI logic and state, separated from PyQt views.
This makes them easy to test without requiring a GUI.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

from gui_framework.events.bus import get_event_bus
from gui_framework.state.store import get_store


class ObservableProperty:
    """
    Property descriptor for observable properties.

    Creates properties that notify observers when their value changes.
    This enables automatic UI updates when ViewModel state changes.

    Example:
        >>> class MyViewModel(BaseViewModel):
        ...     count = ObservableProperty("count", default=0)
        ...
        ...     def increment(self):
        ...         self.count += 1  # Observers notified automatically
    """

    def __init__(self, name: str, default: Any = None):
        """
        Initialize observable property.

        Args:
            name: Property name (will be stored as _name)
            default: Default value
        """
        self.public_name = name
        self.private_name = f"_{name}"
        self.default = default
        self.observers: List[Callable[[Any, Any], None]] = []

    def __set_name__(self, owner, name):
        """Called when property is assigned to a class."""
        self.public_name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        """Get property value."""
        if obj is None:
            return self
        return getattr(obj, self.private_name, self.default)

    def __set__(self, obj, value):
        """Set property value and notify observers."""
        old_value = getattr(obj, self.private_name, self.default)
        setattr(obj, self.private_name, value)

        # Notify observers
        if hasattr(obj, "_notify_property_changed"):
            obj._notify_property_changed(self.public_name, old_value, value)


class BaseViewModel(ABC):
    """
    Base class for all ViewModels.

    ViewModels contain UI logic and state in pure Python (no PyQt dependencies).
    This makes them easy to test and maintain.

    Features:
    - Observable properties for automatic UI updates
    - Access to central state store
    - Access to event bus for communication
    - Lifecycle methods (initialize, cleanup)

    Example:
        >>> class CounterViewModel(BaseViewModel):
        ...     count = ObservableProperty("count", default=0)
        ...
        ...     def initialize(self):
        ...         # Setup subscriptions, load data, etc.
        ...         pass
        ...
        ...     def cleanup(self):
        ...         # Clean up resources
        ...         pass
        ...
        ...     def increment(self):
        ...         self.count += 1
    """

    def __init__(self):
        """Initialize base view-model."""
        self._store = get_store()
        self._event_bus = get_event_bus()
        self._property_observers: Dict[str, List[Callable[[Any, Any], None]]] = {}
        self._initialized = False

    def observe_property(
        self, prop_name: str, callback: Callable[[Any, Any], None]
    ) -> None:
        """
        Observe a property for changes.

        The callback will be invoked whenever the property value changes,
        receiving the old and new values.

        Args:
            prop_name: Name of the property to observe
            callback: Function to call when property changes.
                     Signature: callback(old_value, new_value)

        Example:
            >>> def on_count_changed(old, new):
            ...     print(f"Count changed from {old} to {new}")
            >>>
            >>> vm = CounterViewModel()
            >>> vm.observe_property("count", on_count_changed)
        """
        if prop_name not in self._property_observers:
            self._property_observers[prop_name] = []
        if callback not in self._property_observers[prop_name]:
            self._property_observers[prop_name].append(callback)

    def unobserve_property(
        self, prop_name: str, callback: Callable[[Any, Any], None]
    ) -> None:
        """
        Stop observing a property.

        Args:
            prop_name: Name of the property
            callback: The callback to remove
        """
        if prop_name in self._property_observers:
            if callback in self._property_observers[prop_name]:
                self._property_observers[prop_name].remove(callback)

    def _notify_property_changed(
        self, prop_name: str, old_value: Any, new_value: Any
    ) -> None:
        """
        Notify observers of property change.

        Called automatically by ObservableProperty when value changes.

        Args:
            prop_name: Name of the property that changed
            old_value: Previous value
            new_value: New value
        """
        if prop_name in self._property_observers:
            for callback in self._property_observers[prop_name][
                :
            ]:  # Copy to avoid modification during iteration
                try:
                    callback(old_value, new_value)
                except Exception as e:
                    print(f"Error in property observer for {prop_name}: {e}")

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the view-model.

        Called when the view is shown. Use this to:
        - Subscribe to state changes
        - Subscribe to events
        - Load initial data
        - Set up resources

        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up resources.

        Called when the view is closed. Use this to:
        - Unsubscribe from events
        - Release resources
        - Save state

        Must be implemented by subclasses.
        """
        pass

    def is_initialized(self) -> bool:
        """Check if view-model has been initialized."""
        return self._initialized

    def _mark_initialized(self) -> None:
        """Mark view-model as initialized (called by framework)."""
        self._initialized = True
