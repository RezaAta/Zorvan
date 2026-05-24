import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for adapter test")

from gui_framework.legacy import ReplaceNodeDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_replace_node_adapter_constructs_and_execs(qapp):
    dlg = ReplaceNodeDialog()
    assert hasattr(dlg, "exec")
    # Avoid blocking QDialog.exec() in headless tests; ensure the method exists but don't call it.
    # Instead, verify selected_type() is callable and close() works.
    try:
        _ = dlg.selected_type()
    except Exception:
        pytest.fail("selected_type() raised")
    dlg.close()
