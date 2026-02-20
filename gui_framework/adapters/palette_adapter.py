"""
Palette Adapter - Bridges MVVM CombinedNodePaletteViewModel with legacy CombinedNodePalette.

This adapter enables incremental migration from the legacy node palette
to the MVVM pattern by translating between the two systems.
"""

import logging
from typing import TYPE_CHECKING, Optional

from ..events.bus import Event, EventType, get_event_bus
from ..viewmodels.combined_node_palette_viewmodel import CombinedNodePaletteViewModel

if TYPE_CHECKING:
    from zorvan.GUI.combined_node_palette import CombinedNodePalette
    from zorvan.GUI.main_window import MainWindow

logger = logging.getLogger(__name__)


class PaletteAdapter:
    """
    Adapter that bridges MVVM CombinedNodePaletteViewModel with legacy CombinedNodePalette.

    This allows the new MVVM components to interact with the palette while
    the legacy widget handles actual node creation and drag-drop.

    Usage:
        adapter = PaletteAdapter(main_window)
        adapter.connect()  # Wire up signals

        # Now palette events are published to MVVM EventBus
    """

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize the palette adapter.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window
        self.event_bus = get_event_bus()

        # Create the MVVM ViewModel
        self.viewmodel = CombinedNodePaletteViewModel()
        self.viewmodel.initialize()

    @property
    def palette(self) -> Optional["CombinedNodePalette"]:
        """Access the legacy palette from main window."""
        return getattr(self.main_window, "combined_palette", None) or getattr(
            self.main_window, "palette", None
        )

    def connect(self):
        """Wire up event subscriptions between MVVM and legacy systems."""
        # Wire ViewModel create handler to open custom node dialog
        self.viewmodel.add_create_handler(self._on_create_custom_node)

        # Wire ViewModel select handler to publish event
        self.viewmodel.add_select_handler(self._on_node_selected)

        logger.debug("PaletteAdapter connected")

    def disconnect(self):
        """Cleanup resources."""
        try:
            self.viewmodel.cleanup()
        except Exception:
            pass

        logger.debug("PaletteAdapter disconnected")

    def _on_create_custom_node(self):
        """Handle create custom node request from MVVM ViewModel."""
        try:
            # Try to open the custom node dialog via main window
            if hasattr(self.main_window, "dialog_controller"):
                dialog_controller = self.main_window.dialog_controller
                if hasattr(dialog_controller, "show_custom_node_dialog"):
                    dialog_controller.show_custom_node_dialog()
                    return

            # Fallback to legacy method
            if hasattr(self.main_window, "on_create_custom_node"):
                self.main_window.on_create_custom_node()
                return

            # Try direct dialog creation
            from zorvan.GUI.custom_node_dialog import CustomNodeDialog

            dlg = CustomNodeDialog(parent=self.main_window)
            dlg.exec()

        except Exception as e:
            logger.warning("Failed to open custom node dialog: %s", e)

    def _on_node_selected(self, node_type: str):
        """Handle node selection from palette."""
        # Publish event for other MVVM components
        self.event_bus.publish(
            Event(
                type=EventType.NODE_SELECTED,
                payload={"node_type": node_type, "source": "palette"},
            )
        )

    def get_categories(self):
        """Get available node categories."""
        return self.viewmodel.get_categories()

    def set_search_text(self, text: str):
        """Set search filter text."""
        self.viewmodel.set_search_text(text)

        # Also update legacy palette search if available
        try:
            if self.palette and hasattr(self.palette, "search_bar"):
                self.palette.search_bar.setText(text)
        except Exception:
            pass
