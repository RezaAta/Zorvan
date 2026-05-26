"""Theme support for gui_framework.

This module exposes the compatibility theme manager wrapper through the new framework API.
"""

from .legacy import ThemeManager, _is_test_env, get_theme_manager

if get_theme_manager is None or ThemeManager is None:
    raise ImportError("Legacy theme backend not available")

__all__ = ["get_theme_manager", "ThemeManager", "_is_test_env"]
