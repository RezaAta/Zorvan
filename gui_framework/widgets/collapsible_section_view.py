"""
CollapsibleSection View - PyQt6 UI for collapsible sections.

This is a proof-of-concept migration from the old CollapsibleSection widget
to the new MVVM framework.
"""

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QSizePolicy, QToolButton, QVBoxLayout, QWidget

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QWidget = object

from gui_framework.views.base import BaseView

from .collapsible_section_viewmodel import CollapsibleSectionViewModel


class CollapsibleSectionView(BaseView):
    """
    PyQt6 view for collapsible section widget.

    A simple collapsible section with a header button that toggles visibility
    of the provided content widget. This is the new MVVM version of the
    original CollapsibleSection widget.

    Example:
        >>> from PyQt6.QtWidgets import QLabel
        >>> content = QLabel("Hidden content")
        >>> vm = CollapsibleSectionViewModel(title="Settings", expanded=True)
        >>> view = CollapsibleSectionView(vm, content_widget=content)
        >>> view.show()
    """

    def __init__(
        self,
        viewmodel: CollapsibleSectionViewModel,
        content_widget: "QWidget" = None,
        parent=None,
    ):
        """
        Initialize the collapsible section view.

        Args:
            viewmodel: The CollapsibleSectionViewModel to bind to
            content_widget: The widget to show/hide when toggling
            parent: Optional parent widget
        """
        self.content_widget = content_widget
        super().__init__(viewmodel, parent)
        self._setup_ui()

    def _bind_viewmodel(self) -> None:
        """
        Bind view to viewmodel properties.

        Observe the viewmodel properties and update UI when they change.
        """
        # Observe title changes
        self._viewmodel.observe_property("title", self._on_title_changed)

        # Observe expanded state changes
        self._viewmodel.observe_property("is_expanded", self._on_expanded_changed)

    def _setup_ui(self) -> None:
        """
        Setup PyQt UI widgets.

        Creates the toggle button and lays out the content widget.
        """
        if not PYQT_AVAILABLE:
            return

        # Create toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setText(self._viewmodel.title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(self._viewmodel.is_expanded)
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )

        # Make header occupy full horizontal width
        self.toggle_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # Apply styling
        self._apply_theme()

        # Set font
        self.toggle_button.setFont(
            QFont(
                self.toggle_button.font().family(),
                self.toggle_button.font().pointSize(),
                QFont.Weight.Bold,
            )
        )

        # Set arrow
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow
            if self._viewmodel.is_expanded
            else Qt.ArrowType.RightArrow
        )

        # Connect button to viewmodel
        self.toggle_button.toggled.connect(self._on_button_toggled)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_button)

        if self.content_widget:
            layout.addWidget(self.content_widget)
            self.content_widget.setVisible(self._viewmodel.is_expanded)

    def _apply_theme(self) -> None:
        """Apply theme styling to the toggle button."""
        try:
            # Try to use theme manager if available
            from ComputationalGraphs.GUI.theme import get_theme_manager

            tm = get_theme_manager()
            header = tm.get_color("header_bg", "#239483").name()
            txt = tm.get_color("text").name()
            self.toggle_button.setStyleSheet(
                f"QToolButton {{ text-align: left; padding: 6px 8px; "
                f"border-radius: 6px; font-weight: bold; }} "
                f"QToolButton:checked {{ background-color: {header}; color: {txt}; }} "
            )

            # Subscribe to theme changes
            tm.theme_changed.connect(self._on_theme_changed)
        except Exception:
            # Fallback styling if theme manager not available
            self.toggle_button.setStyleSheet(
                "QToolButton { text-align: left; padding: 6px 8px; "
                "border-radius: 6px; font-weight: bold; } "
                "QToolButton:checked { background-color: #239483; color: white; }"
            )

    def _on_theme_changed(self) -> None:
        """Update styling when theme changes."""
        self._apply_theme()

    def _on_title_changed(self, old_title: str, new_title: str) -> None:
        """
        React to title changes in the viewmodel.

        Args:
            old_title: Previous title
            new_title: New title
        """
        if PYQT_AVAILABLE and hasattr(self, "toggle_button"):
            self.toggle_button.setText(new_title)

    def _on_expanded_changed(self, old_expanded: bool, new_expanded: bool) -> None:
        """
        React to expanded state changes in the viewmodel.

        Args:
            old_expanded: Previous expanded state
            new_expanded: New expanded state
        """
        if not PYQT_AVAILABLE:
            return

        if hasattr(self, "toggle_button"):
            # Update button checked state (without triggering signal)
            self.toggle_button.blockSignals(True)
            self.toggle_button.setChecked(new_expanded)
            self.toggle_button.blockSignals(False)

            # Update arrow
            self.toggle_button.setArrowType(
                Qt.ArrowType.DownArrow if new_expanded else Qt.ArrowType.RightArrow
            )

        # Update content visibility
        if self.content_widget:
            self.content_widget.setVisible(new_expanded)

    def _on_button_toggled(self, checked: bool) -> None:
        """
        Handle button toggle event.

        Delegate to the viewmodel to update state.

        Args:
            checked: New checked state
        """
        # Only update if different from viewmodel state
        # (prevents circular updates)
        if checked != self._viewmodel.is_expanded:
            if checked:
                self._viewmodel.expand()
            else:
                self._viewmodel.collapse()
