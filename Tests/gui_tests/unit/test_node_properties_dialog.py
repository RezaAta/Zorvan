import pytest

from gui_framework.viewmodels.dialogs.node_properties_viewmodel import (
    NodePropertiesViewModel,
)

try:
    from gui_framework.views.dialogs.node_properties_dialog import NodePropertiesDialog

    PYQT = True
except Exception:
    PYQT = False


def test_node_properties_viewmodel_basic():
    vm = NodePropertiesViewModel(
        node_id="n1", name="A", color="#00FF00", description="d"
    )
    assert vm.get_node_id() == "n1"
    assert vm.get_name() == "A"
    assert vm.get_color() == "#00FF00"
    assert vm.get_description() == "d"

    vm.set_name("B")
    assert vm.get_name() == "B"
    vm.set_color(None)
    assert vm.get_color() is None
    vm.set_description("new")
    assert vm.get_description() == "new"


@pytest.mark.skipif(not PYQT, reason="PyQt6 not available")
def test_node_properties_dialog_bindings(qapp):
    vm = NodePropertiesViewModel(
        node_id="n1", name="NodeA", color="#ABCDEF", description="desc"
    )
    dialog = NodePropertiesDialog(vm)

    # UI should reflect initial VM state
    assert dialog.name_edit.text() == "NodeA"
    assert dialog.color_edit.text() == "#ABCDEF"
    assert dialog.desc_edit.toPlainText() == "desc"

    # Simulate user changing values
    dialog.name_edit.setText("NodeB")
    dialog.color_edit.setText("#000000")
    dialog.desc_edit.setPlainText("changed")

    # Apply (preview) without closing
    # Create a sample node to apply to
    class DummyNode:
        def __init__(self):
            self.name = ""
            self.color = None
            self.description = ""

    node = DummyNode()
    # Recreate dialog bound to target node
    dialog = NodePropertiesDialog(vm, None, target_node=node)

    dialog.name_edit.setText("NodeB")
    dialog.color_edit.setText("#000000")
    dialog.desc_edit.setPlainText("changed")

    dialog._on_apply()

    # VM should reflect the changes and the node updated
    assert vm.get_name() == "NodeB"
    assert vm.get_color() == "#000000"
    assert vm.get_description() == "changed"

    assert node.name == "NodeB"
    assert node.color == "#000000"
    assert node.description == "changed"
