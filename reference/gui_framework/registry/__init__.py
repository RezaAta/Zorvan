"""
Widget registry module.

Provides plugin system for registering widgets (ViewModel + View pairs).
"""

from .widget_registry import WidgetRegistry, get_widget_registry

__all__ = ["WidgetRegistry", "get_widget_registry"]
