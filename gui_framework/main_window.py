"""Transitional `MainWindow` entrypoint for the new GUI framework.

This class currently wraps the transitional compatibility layer while enabling
registration with the new `gui_framework.window.manager.WindowManager`.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import QApplication

from .legacy import LegacyMainWindow
from gui_framework.window.manager import get_window_manager

logger = logging.getLogger(__name__)


class MainWindow(LegacyMainWindow):
    """Wrapper around the legacy MainWindow that registers with WindowManager."""

    def __init__(self, *args, window_name: str = "main", **kwargs):
        super().__init__(*args, **kwargs)
        self._window_name = window_name
        self._window_manager = self._register_window()

    def _register_window(self) -> Optional[object]:
        try:
            manager = get_window_manager(QApplication.instance())
        except Exception as exc:
            logger.debug(
                "gui_framework.MainWindow: WindowManager unavailable, skipping registration: %s",
                exc,
            )
            return None

        try:
            manager.register_main_window(self._window_name, self)
        except ValueError as exc:
            logger.debug(
                "gui_framework.MainWindow: could not register window '%s': %s",
                self._window_name,
                exc,
            )
        return manager

    @property
    def window_name(self) -> str:
        return self._window_name
