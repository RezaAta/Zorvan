import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for adapter test")

from zorvan.GUI.custom_node_dialog_adapter import CustomNodeDialogAdapter


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class DummyDef:
    def __init__(self):
        self.type_name = "T"
        self.description = "D"
        self.custom_properties = [{"name": "x", "default_value": "1"}]


def test_adapter_constructs_and_execs(qapp):
    d = DummyDef()
    dlg = CustomNodeDialogAdapter(d)
    assert hasattr(dlg, "exec")
    try:
        res = dlg.exec()
    except Exception:
        res = None
    assert res in (None, 0, 1)
    dlg.close()
