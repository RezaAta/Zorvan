"""MVVM Backprop dialog: binds to BackpropViewModel."""

try:
    from PyQt6.QtWidgets import (
        QDialog,
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
    )

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

from ...viewmodels.base import BaseViewModel

if PYQT_AVAILABLE:
    from gui_framework.viewmodels.dialogs.backprop_viewmodel import BackpropViewModel

    from ..base import BaseView

    class BackpropDialog(QDialog, BaseView):
        def __init__(self, viewmodel: BaseViewModel, parent=None):
            QDialog.__init__(self, parent)
            BaseView.__init__(self, viewmodel, parent)
            self.setWindowTitle("Add Backpropagation")
            self.setMinimumWidth(360)

            self._setup_ui()

            # Bind synchronously for tests when viewmodel already initialized
            try:
                self._bind_viewmodel()
            except Exception:
                pass

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            self.lr_spin = QDoubleSpinBox()
            self.lr_spin.setRange(0.0001, 10.0)
            self.lr_spin.setValue(0.01)
            self.lr_spin.setDecimals(4)
            self.lr_spin.setSingleStep(0.01)

            form.addRow(QLabel("Learning Rate:"), self.lr_spin)
            layout.addLayout(form)

            btn_layout = QHBoxLayout()
            self.add_btn = QPushButton("Add Backpropagation")
            self.add_btn.clicked.connect(self._on_add)
            btn_layout.addWidget(self.add_btn)

            self.remove_btn = QPushButton("Remove Backpropagation")
            self.remove_btn.clicked.connect(self._on_remove)
            btn_layout.addWidget(self.remove_btn)

            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(self.cancel_btn)

            layout.addLayout(btn_layout)

        def _bind_viewmodel(self):
            vm: BackpropViewModel = self.get_viewmodel()
            # Initialize UI from VM
            try:
                self.lr_spin.setValue(vm.get_learning_rate())
            except Exception:
                pass

            # Observe learning rate changes
            try:
                vm.observe_property("learning_rate", self._on_lr_changed)
            except Exception:
                pass

        def _on_lr_changed(self, old, new):
            try:
                if self.lr_spin.value() != float(new):
                    self.lr_spin.setValue(float(new))
            except Exception:
                pass

        def _on_add(self):
            vm: BackpropViewModel = self.get_viewmodel()
            try:
                vm.set_learning_rate(self.lr_spin.value())
                ok = vm.add_backprop()
                if ok:
                    self.accept()
            except Exception:
                pass

        def _on_remove(self):
            vm: BackpropViewModel = self.get_viewmodel()
            try:
                vm.remove_backprop()
                self.accept()
            except Exception:
                pass

        def get_graph(self):
            return self.get_viewmodel().get_generated_graph()

else:

    class BackpropDialog:
        def __init__(self, vm, parent=None):
            self.viewmodel = vm

        def exec(self):
            return 0

        def get_graph(self):
            return self.viewmodel.get_generated_graph()


# Make concrete
if PYQT_AVAILABLE:
    try:
        BackpropDialog.__abstractmethods__ = set()
    except Exception:
        pass
