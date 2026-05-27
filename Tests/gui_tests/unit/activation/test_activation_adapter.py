import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for adapter tests")

from gui_framework.legacy import ActivationDialog


def test_activation_adapter_constructs_and_returns_selection(qtbot):
    dlg = ActivationDialog()
    qtbot.addWidget(dlg._dlg)
    # Don't call exec() (blocking); instead use internals to simulate selection
    try:
        if hasattr(dlg, "_dlg") and hasattr(dlg._dlg, "list_widget"):
            dlg._dlg.list_widget.setCurrentRow(0)
            dlg._dlg._on_accept()
            sel = dlg.selected()
            assert sel in ("Sigmoid", "ReLU", "Linear", "Tanh")
    finally:
        dlg.close()
