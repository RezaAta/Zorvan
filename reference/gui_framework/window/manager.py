"""
Window manager for application lifecycle coordination.

Manages top-level windows and coordinates application lifecycle.
"""

from typing import TYPE_CHECKING, Dict, Optional

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QApplication = None
    QMainWindow = object

from gui_framework.registry.widget_registry import get_widget_registry


class WindowManager:
    """
    Manages top-level windows and application lifecycle.

    Provides centralized coordination of:
    - Window registration and lifecycle
    - Active window tracking
    - Application shutdown

    Example:
        >>> app = QApplication([])
        >>> manager = get_window_manager(app)
        >>>
        >>> main_window = MainWindow()
        >>> manager.register_main_window("main", main_window)
        >>> manager.show_window("main")
    """

    def __init__(self, app: Optional[QApplication] = None):
        """
        Initialize window manager.

        Args:
            app: QApplication instance (required for GUI operations)
        """
        self._app = app
        self._windows: Dict[str, QMainWindow] = {}
        self._active_window: Optional[str] = None
        self._registry = get_widget_registry()

    def register_main_window(self, name: str, window: QMainWindow) -> None:
        """
        Register a main window.

        Args:
            name: Unique window identifier
            window: QMainWindow instance

        Example:
            >>> manager.register_main_window("main", main_window)
        """
        if name in self._windows:
            raise ValueError(f"Window '{name}' is already registered")

        self._windows[name] = window

        # Set as active if first window
        if self._active_window is None:
            self._active_window = name

    def unregister_window(self, name: str) -> None:
        """
        Unregister a window.

        Args:
            name: Window identifier
        """
        if name in self._windows:
            del self._windows[name]

            if self._active_window == name:
                # Set active to another window if available
                self._active_window = next(iter(self._windows.keys()), None)

    def show_window(self, name: str) -> None:
        """
        Show a registered window.

        Args:
            name: Window identifier

        Raises:
            ValueError: If window name is not registered
        """
        if name not in self._windows:
            raise ValueError(f"Window '{name}' is not registered")

        window = self._windows[name]
        window.show()
        self._active_window = name

    def hide_window(self, name: str) -> None:
        """
        Hide a registered window.

        Args:
            name: Window identifier
        """
        if name in self._windows:
            self._windows[name].hide()

    def close_window(self, name: str) -> None:
        """
        Close a registered window.

        Args:
            name: Window identifier
        """
        if name in self._windows:
            window = self._windows[name]
            window.close()
            self.unregister_window(name)

    def get_window(self, name: str) -> Optional[QMainWindow]:
        """
        Get a registered window.

        Args:
            name: Window identifier

        Returns:
            Window instance or None if not found
        """
        return self._windows.get(name)

    def get_active_window(self) -> Optional[QMainWindow]:
        """
        Get currently active window.

        Returns:
            Active window instance or None
        """
        if self._active_window:
            return self._windows.get(self._active_window)
        return None

    def get_active_window_name(self) -> Optional[str]:
        """
        Get name of currently active window.

        Returns:
            Active window name or None
        """
        return self._active_window

    def get_all_windows(self) -> Dict[str, QMainWindow]:
        """
        Get all registered windows.

        Returns:
            Dictionary mapping window names to instances
        """
        return self._windows.copy()

    def get_window_count(self) -> int:
        """
        Get number of registered windows.

        Returns:
            Number of windows
        """
        return len(self._windows)

    def shutdown(self) -> None:
        """
        Shutdown application.

        Closes all windows and quits the application.
        """
        # Close all windows
        for window in list(self._windows.values()):
            window.close()

        self._windows.clear()
        self._active_window = None

        # Quit application
        if self._app and PYQT_AVAILABLE:
            self._app.quit()

    def get_registry(self):
        """
        Get the widget registry.

        Returns:
            WidgetRegistry instance
        """
        return self._registry


# Singleton instance
_manager: Optional[WindowManager] = None


def get_window_manager(app: Optional[QApplication] = None) -> WindowManager:
    """
    Get the global window manager singleton.

    Args:
        app: QApplication instance (required on first call)

    Returns:
        The global WindowManager instance

    Example:
        >>> app = QApplication([])
        >>> manager = get_window_manager(app)
    """
    global _manager
    if _manager is None:
        if app is None and PYQT_AVAILABLE:
            raise ValueError(
                "QApplication instance required for first call to get_window_manager"
            )
        _manager = WindowManager(app)
    return _manager
