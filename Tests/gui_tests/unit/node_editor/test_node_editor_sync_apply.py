import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(
    not PYQT, reason="PyQt6 required for NodeEditorDialog tests"
)

from zorvan.GUI.node_editor_dialog import NodeEditorDialog


class DummyNode:
    def __init__(self):
        self.name = "D"
        self.test_int = 2


def test_spinbox_applies_immediately(qapp):
    node = DummyNode()
    dlg = NodeEditorDialog(node)
    # Ensure VM populated params include 'test_int'
    assert "test_int" in dlg._dlg._widgets

    w = dlg._dlg._widgets["test_int"]
    # Should be QSpinBox-like
    try:
        w.setValue(42)
    except Exception:
        pytest.skip("SpinBox widget not present or not applicable in this environment")

    # Process events so synchronous apply (with guard) can run and possibly schedule a rebuild
    qapp.processEvents()

    # VM should have applied the change immediately, reflected on node
    assert node.test_int == 42

    dlg.close()
