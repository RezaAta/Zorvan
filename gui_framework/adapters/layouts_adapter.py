"""
Layouts Adapter - Bridges MVVM LayoutsView with legacy GraphLayoutController.

This adapter enables incremental migration from the legacy layout controls
to the MVVM pattern by translating between the two systems.
"""

import logging
from typing import TYPE_CHECKING, Optional

from ..events.bus import Event, EventType, get_event_bus

if TYPE_CHECKING:
    from ComputationalGraphs.GUI.controllers.graph_layout_controller import (
        GraphLayoutController,
    )
    from ComputationalGraphs.GUI.main_window import MainWindow

logger = logging.getLogger(__name__)


class LayoutsAdapter:
    """
    Adapter that bridges MVVM LayoutsView with legacy GraphLayoutController.

    This allows the new MVVM LayoutsView to apply layouts while
    the legacy controller handles actual layout computation.

    Usage:
        adapter = LayoutsAdapter(main_window)
        adapter.connect()  # Wire up signals

        # Now layout events are forwarded to legacy controller
    """

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize the layouts adapter.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window
        self.event_bus = get_event_bus()
        self._layouts_view = None

    @property
    def layout_controller(self) -> Optional["GraphLayoutController"]:
        """Access the legacy graph layout controller."""
        return getattr(self.main_window, "graph_layout_controller", None)

    @property
    def canvas_viewmodel(self):
        """Access the CanvasViewModel if available."""
        return getattr(self.main_window, "canvas_viewmodel", None)

    def connect(self):
        """Wire up event subscriptions."""
        # Subscribe to layout events
        self.event_bus.subscribe(EventType.LAYOUT_APPLIED, self._on_layout_applied)

        logger.debug("LayoutsAdapter connected")

    def disconnect(self):
        """Cleanup resources."""
        self.event_bus.unsubscribe(EventType.LAYOUT_APPLIED, self._on_layout_applied)
        logger.debug("LayoutsAdapter disconnected")

    def _on_layout_applied(self, event: Event):
        """Handle layout applied event."""
        payload = event.payload or {}
        algorithm = payload.get("algorithm")
        if algorithm:
            logger.debug("Layout applied: %s", algorithm)

    def apply_layout(self, algorithm: str, direction: str = "LR", spacing: int = 150):
        """Apply a layout algorithm.

        Args:
            algorithm: Layout algorithm name (sugiyama, tree, grid, etc.)
            direction: Layout direction (LR, TB, etc.)
            spacing: Node spacing in pixels
        """
        try:
            mw = self.main_window

            # If a spacing value is provided, ensure the UI spin reflects it
            if spacing is not None and hasattr(mw, "layout_spacing_spin"):
                try:
                    mw.layout_spacing_spin.setValue(int(spacing))
                except Exception:
                    pass

            # If a direction value is provided, set the combo appropriately
            if direction and hasattr(mw, "layout_direction_combo"):
                try:
                    # Accept both 'LR'/'TB' and textual variants
                    if direction.upper().startswith("T") or "Top" in str(direction):
                        mw.layout_direction_combo.setCurrentIndex(1)
                    else:
                        mw.layout_direction_combo.setCurrentIndex(0)
                except Exception:
                    pass

            # Prefer calling the controller's apply_graph_layout (correct name)
            if self.layout_controller and hasattr(
                self.layout_controller, "apply_graph_layout"
            ):
                self.layout_controller.apply_graph_layout(algorithm, spacing)

            # Fallback to main window helper
            elif hasattr(mw, "apply_graph_layout"):
                mw.apply_graph_layout(algorithm, spacing)

            else:
                logger.warning("No layout controller available")
                return

            # Publish event
            self.event_bus.publish(
                Event(
                    type=EventType.LAYOUT_APPLIED,
                    payload={
                        "algorithm": algorithm,
                        "direction": direction,
                        "spacing": spacing,
                    },
                )
            )
        except Exception as e:
            logger.warning("Failed to apply layout: %s", e)

    def create_layouts_view(self, parent=None):
        """Create and return a LayoutsView widget.

        Args:
            parent: Parent widget

        Returns:
            LayoutsView widget or None if not available
        """
        try:
            from ..views.layouts_view import PYQT_AVAILABLE, LayoutsView

            if not PYQT_AVAILABLE:
                return None

            # Get or create canvas viewmodel
            viewmodel = self.canvas_viewmodel
            if viewmodel is None:
                # Create a minimal viewmodel wrapper that forwards to legacy
                viewmodel = self._create_layout_viewmodel_wrapper()

            self._layouts_view = LayoutsView(viewmodel, parent=parent)
            return self._layouts_view
        except Exception as e:
            logger.warning("Failed to create LayoutsView: %s", e)
            return None

    def _create_layout_viewmodel_wrapper(self):
        """Create a minimal viewmodel wrapper for layout operations."""
        adapter = self

        class LayoutViewModelWrapper:
            """Minimal wrapper to forward layout calls to adapter."""

            def __init__(self):
                self._initialized = True

            def apply_layout(
                self, algorithm: str, direction: str = "LR", spacing: int = 150
            ):
                adapter.apply_layout(algorithm, direction, spacing)

            def get_viewmodel(self):
                return self

            def is_initialized(self):
                """Required by BaseView."""
                return self._initialized

            def initialize(self):
                """Required by BaseView."""
                self._initialized = True

        return LayoutViewModelWrapper()

    @property
    def layouts_view(self):
        """Get the LayoutsView widget if created."""
        return self._layouts_view
