import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for view tests")

from gui_framework.viewmodels.dialogs.backprop_config_viewmodel import (
    BackpropConfigViewModel,
)
from gui_framework.views.dialogs.backprop_config_dialog import BackpropConfigDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_backprop_config_view_binds_to_vm(qapp):
    vm = BackpropConfigViewModel(learning_rate=0.03, use_forward=False)
    vm.initialize()

    dlg = BackpropConfigDialog(vm)

    # UI should reflect VM
    assert dlg.lr_spin.value() == pytest.approx(0.03)
    assert dlg.use_forward_checkbox.isChecked() is False

    # Change UI -> VM
    dlg.lr_spin.setValue(0.08)
    dlg.use_forward_checkbox.setChecked(True)

    # Process events to allow signals to propagate
    from PyQt6.QtWidgets import QApplication

    QApplication.processEvents()

    assert vm.get_learning_rate() == pytest.approx(0.08)
    assert vm.get_use_forward() is True

    # Change VM -> UI
    vm.set_learning_rate(0.11)
    vm.set_use_forward(False)
    QApplication.processEvents()

    assert dlg.lr_spin.value() == pytest.approx(0.11)
    assert dlg.use_forward_checkbox.isChecked() is False

    dlg.close()
