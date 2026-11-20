"""
GUI Framework - MVVM Architecture for ComputationalGraphs

This package provides the foundational MVVM framework for the GUI,
including state management, event handling, and base classes.
"""

from .examples_loader import ExamplesLoader
from .main_window import MainWindow
from .theme import ThemeManager, _is_test_env, get_theme_manager
from .window.manager import get_window_manager

__all__ = [
    "MainWindow",
    "ExamplesLoader",
    "ThemeManager",
    "get_window_manager",
    "get_theme_manager",
    "_is_test_env",
]

__version__ = "0.1.0"
