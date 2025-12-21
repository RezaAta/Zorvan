"""
Integration tests for BackpropConfigDialog.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from gui_framework.views.dialogs.backprop_config_dialog import BackpropConfigDialog


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_backprop_config_dialog_accepts(qapp):
    dlg = BackpropConfigDialog()
    dlg.lr_spin.setValue(0.05)
    dlg.use_forward_checkbox.setChecked(True)

    dlg._on_accept()

    cfg = dlg.get_config()
    assert cfg is not None
    assert cfg["learning_rate"] == 0.05
    assert cfg["use_forward"] is True

    dlg.close()
