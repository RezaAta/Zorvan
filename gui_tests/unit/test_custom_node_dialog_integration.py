import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.combined_node_palette import CombinedNodePalette
from ComputationalGraphs.GUI.custom_node_manager import get_custom_node_manager
from gui_framework.viewmodels.dialogs.custom_node_viewmodel import CustomNodeViewModel
from gui_framework.views.dialogs.custom_node_dialog import CustomNodeDialog


def test_dialog_save_updates_palette():
    app = QApplication.instance() or QApplication([])
    mgr = get_custom_node_manager()

    # Clean test node if exists
    if mgr.get_definition("TestNodeB"):
        mgr.remove_definition("TestNodeB")

    vm = CustomNodeViewModel()
    vm.set_type_name("TestNodeB")
    vm.set_input_count(1)
    vm.set_batch_size(1)
    vm.set_operation_code("return input1")

    # Palette present and listening
    pal = CombinedNodePalette()

    dlg = CustomNodeDialog(vm)
    dlg.type_name_edit.setText("TestNodeB")
    dlg.operation_edit.setPlainText("return input1")

    # Perform save
    dlg._on_save()

    # Palette should reflect new node
    assert "Custom Nodes" in pal._category_panels
    assert any(
        getattr(w, "node_type", None) == "TestNodeB" for w, c, d in pal._node_widgets
    )

    # cleanup
    mgr.remove_definition("TestNodeB")
