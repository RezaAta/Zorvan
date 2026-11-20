import pytest

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views import node_editor_dialog

HAS_PYQT = getattr(node_editor_dialog, "HAS_PYQT", False)


@pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 not available")
def test_node_editor_parses_list_from_lineedit():
    class Dummy:
        def __init__(self):
            self.name = "d"
            # Short list should render as QLineEdit in the dialog
            self.inputs = [1, 2]

    d = Dummy()
    vm = NodeEditorViewModel(d)
    vm.initialize()

    dlg = node_editor_dialog.NodeEditorDialog(vm)

    # The dialog builds widgets synchronously; inputs should be present
    w = dlg._widgets.get("inputs")
    assert w is not None

    # Set text and apply
    try:
        w.setText("3,4,5")
    except Exception:
        # If it's not a QLineEdit, fall back to plain text api
        try:
            w.setPlainText("3,4,5")
        except Exception:
            pytest.skip("Widget not interactive in test environment")

    # Call OK handler to apply
    dlg._on_ok()

    assert d.inputs == [3, 4, 5]
