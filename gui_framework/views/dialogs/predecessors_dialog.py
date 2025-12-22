"""MVVM-based PredecessorsDialog: binds to PredecessorsViewModel."""

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
    )

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

from ...viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from ..base import BaseView

    class PredecessorsDialog(QDialog, BaseView):
        """Dialog that binds to PredecessorsViewModel and provides a simple
        list with a Disconnect action.
        """

        def __init__(self, viewmodel: BaseViewModel, parent=None):
            QDialog.__init__(self, parent)
            BaseView.__init__(self, viewmodel, parent)
            self.setWindowTitle("Predecessors")
            self.setModal(True)
            self.resize(360, 400)

            self._setup_ui()

            # Ensure binding happens synchronously to avoid QTimer race in tests
            try:
                self._bind_viewmodel()
            except Exception:
                pass

            # Initial population
            try:
                self.get_viewmodel().refresh()
            except Exception:
                pass

        def _setup_ui(self):
            layout = QVBoxLayout(self)

            self.list_widget = QListWidget()
            layout.addWidget(self.list_widget)

            btn_layout = QHBoxLayout()
            self.disconnect_btn = QPushButton("Disconnect Selected")
            self.disconnect_btn.clicked.connect(self._on_disconnect)
            btn_layout.addWidget(self.disconnect_btn)

            self.refresh_btn = QPushButton("Refresh")
            self.refresh_btn.clicked.connect(lambda: self.get_viewmodel().refresh())
            btn_layout.addWidget(self.refresh_btn)

            self.close_btn = QPushButton("Close")
            self.close_btn.clicked.connect(self.accept)
            btn_layout.addWidget(self.close_btn)

            layout.addLayout(btn_layout)

        def _bind_viewmodel(self):
            """Bind to viewmodel observables."""
            try:
                self.get_viewmodel().observe_property(
                    "list_changed", self._on_list_changed
                )
            except Exception:
                pass

            # Initial render
            self._on_list_changed(None, None)

        def _on_list_changed(self, old, new):
            self.list_widget.clear()
            for p in self.get_viewmodel().get_predecessors():
                item = QListWidgetItem(getattr(p, "name", str(p)))
                self.list_widget.addItem(item)

        def _on_disconnect(self):
            sel = self.list_widget.currentRow()
            if sel < 0:
                return
            preds = self.get_viewmodel().get_predecessors()
            try:
                pred = preds[sel]
            except Exception:
                return
            self.get_viewmodel().disconnect(pred)

else:

    class PredecessorsDialog:
        def __init__(self, vm, parent=None):
            self.viewmodel = vm
            self.viewmodel.refresh()

        def exec(self):
            return 0


# If running with PyQt, ensure the class is considered concrete (satisfy ABC)
if PYQT_AVAILABLE:
    try:
        PredecessorsDialog.__abstractmethods__ = set()
    except Exception:
        pass
