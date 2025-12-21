"""
Base View class for PyQt6 views.

Views are thin UI layers that bind to ViewModels for logic and state.
"""

from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING

try:
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QWidget

    PYQT_AVAILABLE = True
except ImportError:
    # Allow import for testing without PyQt6
    PYQT_AVAILABLE = False
    QWidget = object

if TYPE_CHECKING:
    from gui_framework.viewmodels.base import BaseViewModel


if PYQT_AVAILABLE:
    # Combine PyQt wrapper metaclass (type(QWidget)) with ABCMeta so we can
    # use @abstractmethod on a QWidget subclass without causing a metaclass
    # conflict.
    class _CombinedMeta(type(QWidget), ABCMeta):
        """Metaclass that combines PyQt wrapper metaclass and ABCMeta."""

        pass

    class BaseView(QWidget, metaclass=_CombinedMeta):
        """
        Base class for all PyQt6 views.

        Views are thin UI layers that:
        - Bind to ViewModels for logic and state
        - Handle PyQt6-specific UI code
        - React to ViewModel changes
        - Delegate user actions to ViewModel

        The View-ViewModel binding enables:
        - Automatic UI updates when ViewModel state changes
        - Easy testing (test ViewModel without GUI)
        - Clear separation of concerns

        Example:
            >>> class CounterView(BaseView):
            ...     def __init__(self, viewmodel: CounterViewModel, parent=None):
            ...         super().__init__(viewmodel, parent)
            ...         self._setup_ui()
            ...
            ...     def _bind_viewmodel(self):
            ...         # Observe ViewModel properties
            ...         self._viewmodel.observe_property("count", self._on_count_changed)
            ...
            ...     def _setup_ui(self):
            ...         # Create PyQt6 widgets
            ...         self.label = QLabel("0")
            ...         self.button = QPushButton("+")
            ...         self.button.clicked.connect(self._on_increment)
            ...         # ... layout setup ...
            ...
            ...     def _on_count_changed(self, old, new):
            ...         # Update UI when ViewModel changes
            ...         self.label.setText(str(new))
            ...
            ...     def _on_increment(self):
            ...         # Delegate to ViewModel
            ...         self._viewmodel.increment()
        """

        def __init__(self, viewmodel: "BaseViewModel", parent=None):
            """
            Initialize view with viewmodel binding.

            Args:
                viewmodel: The viewmodel to bind to
                parent: Optional parent widget
            """
            super().__init__(parent)
            self._viewmodel = viewmodel
            # Defer binding to allow subclasses to finish initialization
            # (they may set attributes used by _bind_viewmodel).
            # If the viewmodel is already initialized, bind immediately so
            # Views created after ViewModel.initialize() take effect
            # synchronously (useful for tests that don't pump the event loop).
            if hasattr(self, "_viewmodel") and self._viewmodel.is_initialized():
                # Synchronous bind when ViewModel is already initialized
                try:
                    self._bind_viewmodel()
                except Exception:
                    # Avoid failing construction due to binding errors
                    pass
            else:
                # Schedule binding to occur after current call stack
                QTimer.singleShot(0, self._bind_viewmodel)

        @abstractmethod
        def _bind_viewmodel(self) -> None:
            """
            Bind view to viewmodel properties.

            Called once during construction. Use this to:
            - Observe ViewModel properties
            - Set up initial state from ViewModel

            Example:
                >>> def _bind_viewmodel(self):
                ...     self._viewmodel.observe_property("count", self._on_count_changed)
                ...     self._viewmodel.observe_property("enabled", self._on_enabled_changed)
            """
            pass

        @abstractmethod
        def _setup_ui(self) -> None:
            """
            Setup PyQt UI widgets.

            Called after binding. Use this to:
            - Create widgets
            - Set up layouts
            - Connect signals to slots

            Example:
                >>> def _setup_ui(self):
                ...     self.label = QLabel()
                ...     self.button = QPushButton("Click")
                ...     self.button.clicked.connect(self._on_button_clicked)
                ...
                ...     layout = QVBoxLayout(self)
                ...     layout.addWidget(self.label)
                ...     layout.addWidget(self.button)
            """
            pass

        def showEvent(self, event):
            """
            Called when view becomes visible.

            Automatically initializes the viewmodel if not already initialized.
            """
            super().showEvent(event)

            if not self._viewmodel.is_initialized():
                self._viewmodel.initialize()
                self._viewmodel._mark_initialized()

        def closeEvent(self, event):
            """
            Called when view is closed.

            Automatically cleans up the viewmodel.
            """
            self._viewmodel.cleanup()
            super().closeEvent(event)

        def get_viewmodel(self) -> "BaseViewModel":
            """
            Get the bound viewmodel.

            Returns:
                The viewmodel instance
            """
            return self._viewmodel

else:
    # Minimal BaseView for testing without PyQt6
    class BaseView(ABC):
        """Base class for views when PyQt6 is not available (testing only)."""

        def __init__(self, viewmodel: "BaseViewModel", parent=None):
            self._viewmodel = viewmodel
            self._bind_viewmodel()

        @abstractmethod
        def _bind_viewmodel(self) -> None:
            pass

        @abstractmethod
        def _setup_ui(self) -> None:
            pass

        def get_viewmodel(self) -> "BaseViewModel":
            return self._viewmodel
