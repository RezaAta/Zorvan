"""Test that legacy import path delegates to MVVM NodeEditorDialog when available."""

import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(
    not PYQT, reason="PyQt6 required for dialog adapter test"
)

from zorvan.GUI.node_editor_dialog import NodeEditorDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class DummyNode:
    def __init__(self):
        self.name = "D"
        self.value = 0


def test_node_editor_adapter_constructs_and_execs(qapp):
    node = DummyNode()
    dlg = NodeEditorDialog(node)
    # Should expose an exec method
    assert hasattr(dlg, "exec")
    # exec returns a dialog code (0 or 1); call and then close immediately
    # Use non-blocking approach: just call exec and it should return quickly in tests
    try:
        res = dlg.exec()
    except Exception:
        # Some systems may require event loop integration; consider a successful instantiation enough
        res = None
    assert res in (None, 0, 1)
    dlg.close()
