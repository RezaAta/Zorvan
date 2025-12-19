"""
CollapsibleSection ViewModel - Pure Python logic for collapsible sections.

This is a proof-of-concept migration from the old CollapsibleSection widget
to the new MVVM framework.
"""

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class CollapsibleSectionViewModel(BaseViewModel):
    """
    ViewModel for collapsible section widget.
    
    Manages the collapsed/expanded state and provides methods to toggle.
    This is pure Python with no PyQt dependencies, making it easy to test.
    
    Example:
        >>> vm = CollapsibleSectionViewModel(title="Settings", expanded=True)
        >>> vm.initialize()
        >>> assert vm.is_expanded == True
        >>> vm.toggle()
        >>> assert vm.is_expanded == False
    """
    
    # Observable properties
    title = ObservableProperty("title", default="")
    is_expanded = ObservableProperty("is_expanded", default=True)
    
    def __init__(self, title: str = "", expanded: bool = True):
        """
        Initialize the collapsible section view-model.
        
        Args:
            title: Section title text
            expanded: Initial expanded state
        """
        super().__init__()
        self.title = title
        self.is_expanded = expanded
    
    def initialize(self) -> None:
        """
        Initialize the view-model.
        
        Called when the view is shown. Currently no subscriptions needed,
        but this is where we'd subscribe to state changes or events if needed.
        """
        # No state subscriptions needed for this simple widget
        pass
    
    def cleanup(self) -> None:
        """
        Clean up resources.
        
        Called when the view is closed. Currently no cleanup needed,
        but this is where we'd unsubscribe from events if needed.
        """
        # No cleanup needed for this simple widget
        pass
    
    def toggle(self) -> None:
        """
        Toggle the expanded/collapsed state.
        
        This will automatically notify observers (the View) that the
        is_expanded property has changed.
        """
        self.is_expanded = not self.is_expanded
    
    def expand(self) -> None:
        """Set the section to expanded state."""
        self.is_expanded = True
    
    def collapse(self) -> None:
        """Set the section to collapsed state."""
        self.is_expanded = False
    
    def set_title(self, title: str) -> None:
        """
        Change the section title.
        
        Args:
            title: New title text
        """
        self.title = title
