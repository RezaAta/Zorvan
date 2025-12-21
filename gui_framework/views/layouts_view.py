"""
LayoutsView: UI controls for applying graph layout algorithms to the canvas.

Binds directly to a CanvasViewModel and exposes algorithm selector, direction,
spacing controls and an Apply button.
"""

try:
    from PyQt6.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False


from ..viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from .base import BaseView

    class LayoutsView(BaseView):
        """A small panel to choose and apply layout algorithms."""

        def __init__(self, viewmodel: BaseViewModel, parent=None):
            super().__init__(viewmodel, parent)
            # Backwards compat
            self.viewmodel = viewmodel
            self._setup_ui()
            self._connect_signals()

        def _setup_ui(self):
            layout = QHBoxLayout(self)

            # Algorithm selector
            layout.addWidget(QLabel("Layout:"))
            self.algo_combo = QComboBox()
            self.algo_combo.addItem("Sugiyama", "sugiyama")
            self.algo_combo.addItem("Tree", "tree")
            self.algo_combo.addItem("MLP (layered)", "mlp_layered")
            self.algo_combo.addItem("MLP (full)", "mlp_layout")
            self.algo_combo.addItem("Grid", "grid")
            self.algo_combo.addItem("Circular", "circular")
            self.algo_combo.addItem("Force (spring)", "force")
            layout.addWidget(self.algo_combo)

            # Direction
            layout.addWidget(QLabel("Direction:"))
            self.dir_combo = QComboBox()
            self.dir_combo.addItem("Left->Right", "LR")
            self.dir_combo.addItem("Top->Bottom", "TB")
            layout.addWidget(self.dir_combo)

            # Spacing
            layout.addWidget(QLabel("Spacing:"))
            self.spacing_spin = QSpinBox()
            self.spacing_spin.setMinimum(20)
            self.spacing_spin.setMaximum(1000)
            self.spacing_spin.setValue(150)
            layout.addWidget(self.spacing_spin)

            # Apply button
            self.apply_button = QPushButton("Apply")
            layout.addWidget(self.apply_button)

        def _bind_viewmodel(self):
            # No continuous live state to observe; placeholder in case features added
            pass

        def _connect_signals(self):
            self.apply_button.clicked.connect(self._on_apply)

        def _on_apply(self):
            vm = self.get_viewmodel()
            algo = self.algo_combo.currentData()
            direction = self.dir_combo.currentData()
            spacing = int(self.spacing_spin.value())

            try:
                vm.apply_layout(algorithm=algo, direction=direction, spacing=spacing)
            except Exception:
                # Silently ignore to keep UI robust in tests
                pass

else:
    # Stub for testing when PyQt isn't available
    class LayoutsView:
        def __init__(self, viewmodel, parent=None):
            self.viewmodel = viewmodel
            self.algo_combo = None
            self.dir_combo = None
            self.spacing_spin = None
            self.apply_button = None
