"""
Window management module.

Provides window lifecycle coordination and management.
"""

from .manager import WindowManager, get_window_manager

__all__ = ["WindowManager", "get_window_manager"]
