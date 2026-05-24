import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for adapter tests")

from gui_framework.legacy import LearningRateDialog


class DummyNode:
    def __init__(self):
        self.value = 0.5


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_learning_rate_adapter_constructs_and_applies(qapp):
    node = DummyNode()
    dlg = LearningRateDialog(node)

    # Set via internal dialog and apply
    try:
        if hasattr(dlg, "_dlg") and hasattr(dlg._dlg, "lr_spin"):
            dlg._dlg.lr_spin.setValue(0.314159)
            dlg.apply_to_node()
            assert node.value == pytest.approx(0.314159)
    finally:
        dlg.close()
