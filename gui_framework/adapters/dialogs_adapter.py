"""
Dialogs Adapter - Bridges MVVM dialog views with legacy DialogController.

This adapter enables incremental migration from the legacy dialogs
to the MVVM pattern by translating between the two systems.
"""

import logging
from typing import TYPE_CHECKING, Any, Optional

from ..events.bus import Event, EventType, get_event_bus

if TYPE_CHECKING:
    from zorvan.GUI.controllers.dialog_controller import DialogController
    from zorvan.GUI.main_window import MainWindow

logger = logging.getLogger(__name__)


class DialogsAdapter:
    """
    Adapter that bridges MVVM dialog views with legacy DialogController.

    This allows the new MVVM dialogs to be used while
    the legacy controller handles graph modifications.

    Usage:
        adapter = DialogsAdapter(main_window)
        adapter.connect()  # Wire up signals

        # Show dialogs via MVVM
        adapter.show_mlp_dialog()
        adapter.show_backprop_dialog()
    """

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize the dialogs adapter.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window
        self.event_bus = get_event_bus()

    @property
    def dialog_controller(self) -> Optional["DialogController"]:
        """Access the legacy dialog controller."""
        return getattr(self.main_window, "dialog_controller", None)

    def connect(self):
        """Wire up event subscriptions."""
        # Subscribe to dialog events
        self.event_bus.subscribe(EventType.MLP_GENERATED, self._on_mlp_generated)
        self.event_bus.subscribe(EventType.BACKPROP_ADDED, self._on_backprop_added)

        logger.debug("DialogsAdapter connected")

    def disconnect(self):
        """Cleanup resources."""
        self.event_bus.unsubscribe(EventType.MLP_GENERATED, self._on_mlp_generated)
        self.event_bus.unsubscribe(EventType.BACKPROP_ADDED, self._on_backprop_added)
        logger.debug("DialogsAdapter disconnected")

    def _on_mlp_generated(self, event: Event):
        """Handle MLP generated event."""
        payload = event.payload or {}
        logger.debug("MLP generated: %s", payload)

    def _on_backprop_added(self, event: Event):
        """Handle backprop added event."""
        payload = event.payload or {}
        logger.debug("Backprop added: %s", payload)

    def show_mlp_dialog(self) -> Optional[Any]:
        """Show the MLP generator dialog.

        Returns:
            The generated MLP graph or None if cancelled
        """
        try:
            # Try MVVM dialog first
            from ..views.dialogs.mlp_generator_dialog import (
                PYQT_AVAILABLE,
                MLPGeneratorDialog,
            )

            if PYQT_AVAILABLE:
                from ..viewmodels.mlp_generator_viewmodel import MLPGeneratorViewModel

                viewmodel = MLPGeneratorViewModel()
                viewmodel.initialize()

                dialog = MLPGeneratorDialog(viewmodel, parent=self.main_window)
                result = dialog.exec()

                if result and viewmodel.generated_graph:
                    graph = viewmodel.generated_graph

                    # Apply to main window
                    self.main_window.set_graph(graph)
                    self.main_window._visualize_graph_on_canvas(graph)

                    # Publish event
                    self.event_bus.publish(
                        Event(type=EventType.MLP_GENERATED, payload={"graph": graph})
                    )
                    return graph

                return None

        except ImportError:
            pass
        except Exception as e:
            logger.warning("MVVM MLP dialog failed: %s, falling back to legacy", e)

        # Fallback to legacy dialog
        return self._show_legacy_mlp_dialog()

    def _show_legacy_mlp_dialog(self) -> Optional[Any]:
        """Show legacy MLP dialog."""
        try:
            if self.dialog_controller:
                return self.dialog_controller.show_mlp_dialog()
            elif hasattr(self.main_window, "_show_mlp_dialog"):
                return self.main_window._show_mlp_dialog()
        except Exception as e:
            logger.warning("Failed to show legacy MLP dialog: %s", e)
        return None

    def show_backprop_dialog(self) -> bool:
        """Show the backprop configuration dialog.

        Returns:
            True if backprop was added successfully
        """
        try:
            # Try MVVM dialog first
            from ..views.dialogs.backprop_dialog import PYQT_AVAILABLE, BackpropDialog

            if PYQT_AVAILABLE:
                dialog = BackpropDialog(
                    graph=self.main_window.graph, parent=self.main_window
                )
                result = dialog.exec()

                if result:
                    # Publish event
                    self.event_bus.publish(
                        Event(type=EventType.BACKPROP_ADDED, payload={})
                    )
                    return True

                return False

        except ImportError:
            pass
        except Exception as e:
            logger.warning("MVVM Backprop dialog failed: %s, falling back to legacy", e)

        # Fallback to legacy dialog
        return self._show_legacy_backprop_dialog()

    def _show_legacy_backprop_dialog(self) -> bool:
        """Show legacy backprop dialog."""
        try:
            if self.dialog_controller:
                return self.dialog_controller.show_backprop_dialog()
            elif hasattr(self.main_window, "_show_backprop_dialog"):
                return self.main_window._show_backprop_dialog()
        except Exception as e:
            logger.warning("Failed to show legacy backprop dialog: %s", e)
        return False

    def show_preferences_dialog(self) -> bool:
        """Show the preferences dialog.

        Returns:
            True if preferences were changed
        """
        try:
            # Try MVVM dialog first
            from ..views.dialogs.color_preferences_dialog import (
                PYQT_AVAILABLE,
                ColorPreferencesDialog,
            )

            if PYQT_AVAILABLE:
                dialog = ColorPreferencesDialog(parent=self.main_window)
                result = dialog.exec()
                return bool(result)

        except ImportError:
            pass
        except Exception as e:
            logger.warning(
                "MVVM Preferences dialog failed: %s, falling back to legacy", e
            )

        # Fallback to legacy
        try:
            if hasattr(self.main_window, "show_preferences"):
                self.main_window.show_preferences()
                return True
        except Exception as e:
            logger.warning("Failed to show preferences: %s", e)
        return False

    def show_new_graph_dialog(self) -> bool:
        """Show the new graph dialog.

        Returns:
            True if a new graph was created
        """
        try:
            # Try MVVM dialog first
            from ..views.dialogs.new_graph_dialog import PYQT_AVAILABLE, NewGraphDialog

            if PYQT_AVAILABLE:
                dialog = NewGraphDialog(parent=self.main_window)
                result = dialog.exec()

                if result and hasattr(dialog, "created_graph"):
                    graph = dialog.created_graph
                    self.main_window.set_graph(graph)
                    self.main_window._visualize_graph_on_canvas(graph)
                    return True

                return False

        except ImportError:
            pass
        except Exception as e:
            logger.warning(
                "MVVM New Graph dialog failed: %s, falling back to legacy", e
            )

        # Fallback to legacy
        try:
            if hasattr(self.main_window, "_show_new_graph_dialog"):
                self.main_window._show_new_graph_dialog()
                return True
        except Exception as e:
            logger.warning("Failed to show new graph dialog: %s", e)
        return False
