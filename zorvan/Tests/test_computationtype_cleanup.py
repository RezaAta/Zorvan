import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views.node_editor_dialog import NodeEditorDialog
from zorvan.Nodes.InitializableContainerNode import InitializableContainerNode


def test_delete_computationtype_and_render_dialog(qtbot):
    app = QApplication.instance() or QApplication([])
    node = InitializableContainerNode(name="W_test", value=0.5)
    node.gui_pos = (10, 20)
    node.computationType = "basic"

    vm = NodeEditorViewModel(node)
    vm.initialize()

    # Remove the attribute from the instance to simulate its absence
    if hasattr(node, "computationType"):
        delattr(node, "computationType")

    # Reload VM properties and ensure missing attribute is handled gracefully
    vm.load_node(node)
    props = vm.get_properties()
    # The key may exist with value None, or be absent
    assert "computationType" not in props or props.get("computationType") is None

    # Create dialog and ensure it renders; the more-details widget should still exist
    dlg = NodeEditorDialog(vm)
    qtbot.addWidget(dlg)
    assert hasattr(dlg, "_more_widget")
    # Can toggle without errors
    dlg._more_button.click()
    # The computation-type widget may be empty or show an empty string
    comp_widget = dlg._widgets.get("computationType")
    if comp_widget is not None:
        # Accept QLabel or QLineEdit; check it has a text() method and no exception raised
        assert hasattr(comp_widget, "text")
