"""
Widgets package for gui_framework.

Contains ViewModel and View implementations for common widgets.
"""

from .collapsible_section_view import CollapsibleSectionView
from .collapsible_section_viewmodel import CollapsibleSectionViewModel

__all__ = [
    "CollapsibleSectionViewModel",
    "CollapsibleSectionView",
]
