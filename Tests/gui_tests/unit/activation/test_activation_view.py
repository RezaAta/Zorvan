import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for view tests")

from gui_framework.viewmodels.dialogs.activation_viewmodel import ActivationViewModel
from gui_framework.views.dialogs.activation_dialog import ActivationDialog


def test_activation_dialog_populates_and_selects(qtbot):
    vm = ActivationViewModel(available=["Sigmoid", "ReLU"], selected="Sigmoid")
    vm.initialize()
    dlg = ActivationDialog(vm)
    qtbot.addWidget(dlg)

    # initial state
    assert dlg.list_widget.count() == 2

    # simulate user selection
    dlg.list_widget.setCurrentRow(1)
    dlg._on_accept()

    assert vm.get_selected() == "ReLU"

    dlg.close()
