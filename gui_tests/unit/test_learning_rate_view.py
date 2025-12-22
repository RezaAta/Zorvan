import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for view tests")

from gui_framework.viewmodels.dialogs.learning_rate_viewmodel import (
    LearningRateViewModel,
)
from gui_framework.views.dialogs.learning_rate_dialog import LearningRateDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_learning_rate_dialog_binds(qapp):
    vm = LearningRateViewModel(0.07)
    vm.initialize()
    dlg = LearningRateDialog(vm)

    assert dlg.lr_spin.value() == pytest.approx(0.07)

    dlg.lr_spin.setValue(0.09)

    from PyQt6.QtWidgets import QApplication

    QApplication.processEvents()

    assert vm.get_value() == pytest.approx(0.09)

    vm.set_value(0.12)
    QApplication.processEvents()

    assert dlg.lr_spin.value() == pytest.approx(0.12)

    dlg.close()
