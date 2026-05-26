"""
Widget registry for plugin-based extension system.

Allows registering and creating ViewModel+View widget pairs.
"""

from typing import TYPE_CHECKING, Callable, Dict, Tuple, Type

if TYPE_CHECKING:
    from gui_framework.viewmodels.base import BaseViewModel
    from gui_framework.views.base import BaseView


class WidgetRegistry:
    """
    Registry for ViewModel and View pairs.

    Enables plugin-based extension by allowing widgets to be registered
    and created dynamically. This is the foundation for a plugin system.

    Example:
        >>> registry = get_widget_registry()
        >>>
        >>> # Register a widget
        >>> registry.register_widget(
        ...     name="counter",
        ...     viewmodel_cls=CounterViewModel,
        ...     view_cls=CounterView
        ... )
        >>>
        >>> # Create widget instance
        >>> viewmodel, view = registry.create_widget("counter")
    """

    def __init__(self):
        """Initialize empty registry."""
        self._viewmodels: Dict[str, Type["BaseViewModel"]] = {}
        self._views: Dict[str, Type["BaseView"]] = {}
        self._factories: Dict[str, Callable] = {}
        self._metadata: Dict[str, dict] = {}

    def register_widget(
        self,
        name: str,
        viewmodel_cls: Type["BaseViewModel"],
        view_cls: Type["BaseView"],
        factory: Callable = None,
        metadata: dict = None,
    ) -> None:
        """
        Register a widget (ViewModel + View pair).

        Args:
            name: Unique widget name
            viewmodel_cls: ViewModel class
            view_cls: View class
            factory: Optional custom factory function.
                    Signature: factory(**kwargs) -> (viewmodel, view)
            metadata: Optional metadata (description, category, etc.)

        Example:
            >>> registry.register_widget(
            ...     name="counter",
            ...     viewmodel_cls=CounterViewModel,
            ...     view_cls=CounterView,
            ...     metadata={"category": "examples", "description": "Simple counter"}
            ... )
        """
        if name in self._viewmodels:
            raise ValueError(f"Widget '{name}' is already registered")

        self._viewmodels[name] = viewmodel_cls
        self._views[name] = view_cls

        if factory:
            self._factories[name] = factory

        if metadata:
            self._metadata[name] = metadata

    def unregister_widget(self, name: str) -> None:
        """
        Unregister a widget.

        Args:
            name: Widget name to unregister
        """
        if name in self._viewmodels:
            del self._viewmodels[name]
        if name in self._views:
            del self._views[name]
        if name in self._factories:
            del self._factories[name]
        if name in self._metadata:
            del self._metadata[name]

    def create_widget(self, name: str, **kwargs) -> Tuple["BaseViewModel", "BaseView"]:
        """
        Create a widget instance.

        Args:
            name: Name of the registered widget
            **kwargs: Arguments to pass to viewmodel/view constructors

        Returns:
            Tuple of (viewmodel, view)

        Raises:
            ValueError: If widget name is not registered

        Example:
            >>> viewmodel, view = registry.create_widget("counter")
            >>> view.show()
        """
        if name not in self._viewmodels:
            raise ValueError(f"Widget '{name}' is not registered")

        # Use custom factory if provided
        if name in self._factories:
            return self._factories[name](**kwargs)

        # Default creation: viewmodel, then view
        vm_cls = self._viewmodels[name]
        view_cls = self._views[name]

        # Create viewmodel
        viewmodel = vm_cls()

        # Create view with viewmodel
        # Extract 'parent' for view if provided
        parent = kwargs.pop("parent", None)
        view = view_cls(viewmodel, parent=parent)

        return viewmodel, view

    def is_registered(self, name: str) -> bool:
        """
        Check if a widget is registered.

        Args:
            name: Widget name

        Returns:
            True if widget is registered
        """
        return name in self._viewmodels

    def get_registered_widgets(self) -> list:
        """
        Get list of all registered widget names.

        Returns:
            List of widget names
        """
        return list(self._viewmodels.keys())

    def get_widget_metadata(self, name: str) -> dict:
        """
        Get metadata for a widget.

        Args:
            name: Widget name

        Returns:
            Widget metadata dictionary (empty dict if no metadata)
        """
        return self._metadata.get(name, {})

    def get_widgets_by_category(self, category: str) -> list:
        """
        Get all widgets in a category.

        Args:
            category: Category name

        Returns:
            List of widget names in the category
        """
        return [
            name
            for name, meta in self._metadata.items()
            if meta.get("category") == category
        ]


# Singleton instance
_registry: WidgetRegistry = None


def get_widget_registry() -> WidgetRegistry:
    """
    Get the global widget registry singleton.

    Returns:
        The global WidgetRegistry instance

    Example:
        >>> registry = get_widget_registry()
        >>> registry.register_widget("my_widget", MyViewModel, MyView)
    """
    global _registry
    if _registry is None:
        _registry = WidgetRegistry()
    return _registry
