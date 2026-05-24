"""
Examples Loader Adapter - Bridges MVVM ExamplesLoaderViewModel with legacy ExamplesLoader.

This adapter enables incremental migration from the legacy examples loader
to the MVVM pattern by translating between the two systems.
"""

import logging
from typing import TYPE_CHECKING, Optional

from ..events.bus import Event, EventType, get_event_bus
from ..viewmodels.examples_loader_viewmodel import ExamplesLoaderViewModel

if TYPE_CHECKING:
    from gui_framework.examples_loader import ExamplesLoader
    from gui_framework.main_window import MainWindow

logger = logging.getLogger(__name__)


class ExamplesLoaderAdapter:
    """
    Adapter that bridges MVVM ExamplesLoaderViewModel with legacy ExamplesLoader.

    This allows the new MVVM components to list and load examples while
    the legacy loader handles actual graph loading.

    Usage:
        adapter = ExamplesLoaderAdapter(main_window)
        adapter.connect()  # Wire up signals

        # Now example loading triggers MVVM events
    """

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize the examples loader adapter.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window
        self.event_bus = get_event_bus()

        # Get examples repository if available
        repository = getattr(main_window, "examples_repository", None)

        # Create the MVVM ViewModel
        self.viewmodel = ExamplesLoaderViewModel(repository=repository)
        self.viewmodel.initialize()

    @property
    def examples_loader(self) -> Optional["ExamplesLoader"]:
        """Access the legacy examples loader from main window."""
        return getattr(self.main_window, "examples_loader", None)

    def connect(self):
        """Wire up event subscriptions."""
        # Subscribe to graph loaded events
        self.event_bus.subscribe(EventType.GRAPH_LOADED, self._on_graph_loaded)

        logger.debug("ExamplesLoaderAdapter connected")

    def disconnect(self):
        """Cleanup resources."""
        self.event_bus.unsubscribe(EventType.GRAPH_LOADED, self._on_graph_loaded)

        try:
            self.viewmodel.cleanup()
        except Exception:
            pass

        logger.debug("ExamplesLoaderAdapter disconnected")

    def _on_graph_loaded(self, event: Event):
        """Handle graph loaded event."""
        payload = event.payload or {}
        example_name = payload.get("example_name")
        if example_name:
            logger.debug("Example loaded: %s", example_name)

    def list_examples(self):
        """List available examples."""
        return self.viewmodel.list_examples()

    def list_examples_by_category(self):
        """List examples organized by category."""
        return self.viewmodel.list_examples_by_category()

    def build_example(self, name: str):
        """Build and load an example by name."""
        built = self.viewmodel.build_example(name)

        if built is not None:
            # Publish event
            self.event_bus.publish(
                Event(
                    type=EventType.GRAPH_LOADED,
                    payload={"example_name": name, "graph": built},
                )
            )

            # Apply to main window if it's a graph
            try:
                from zorvan.Core.Graph import Graph

                if isinstance(built, Graph):
                    self.main_window.set_graph(built)
                    self.main_window._visualize_graph_on_canvas(built)
                    return True
            except Exception as e:
                logger.warning("Failed to apply example graph: %s", e)

        return built is not None

    def load_legacy_example(self, example_name: str):
        """Load an example using the legacy ExamplesLoader."""
        if self.examples_loader:
            try:
                # Use legacy loader's method if available
                if hasattr(self.examples_loader, "load_example"):
                    graph = self.examples_loader.load_example(example_name)
                    if graph:
                        self.main_window.set_graph(graph)
                        self.main_window._visualize_graph_on_canvas(graph)

                        # Publish event
                        self.event_bus.publish(
                            Event(
                                type=EventType.GRAPH_LOADED,
                                payload={"example_name": example_name, "graph": graph},
                            )
                        )
                        return True
            except Exception as e:
                logger.warning("Failed to load legacy example: %s", e)

        return False
