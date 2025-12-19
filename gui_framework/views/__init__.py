"""
Views module.

Provides base classes and concrete implementations for PyQt6 views (thin UI layer).
"""

from .base import BaseView
from .execution_view import ExecutionView

__all__ = ["BaseView", "ExecutionView"]
