import pytest

from gui_framework.viewmodels.dialogs.new_graph_viewmodel import NewGraphViewModel

try:
    from gui_framework.views.dialogs.new_graph_dialog import NewGraphDialog

    PYQT = True
except Exception:
    PYQT = False


def test_new_graph_viewmodel_basic():
    vm = NewGraphViewModel(name="G1", num_inputs=2, num_outputs=1, graph_type="MLP")
    assert vm.get_name() == "G1"
    assert vm.get_num_inputs() == 2
    assert vm.get_num_outputs() == 1
    assert vm.get_graph_type() == "MLP"

    vm.set_name("G2")
    assert vm.get_name() == "G2"
    vm.set_num_inputs(3)
    assert vm.get_num_inputs() == 3
    vm.set_num_outputs(2)
    assert vm.get_num_outputs() == 2
    vm.set_graph_type("ANFIS")
    assert vm.get_graph_type() == "ANFIS"

    graph = vm.create_graph()
    assert graph["name"] == "G2"
    assert graph["num_inputs"] == 3
    assert graph["num_outputs"] == 2
    assert graph["type"] == "ANFIS"


@pytest.mark.skipif(not PYQT, reason="PyQt6 not available")
def test_new_graph_dialog_bindings(qapp):
    vm = NewGraphViewModel(
        name="InitGraph", num_inputs=4, num_outputs=2, graph_type="MLP"
    )
    dialog = NewGraphDialog(vm)

    # UI reflects initial state
    assert dialog.name_edit.text() == "InitGraph"
    assert dialog.inputs_spin.value() == 4
    assert dialog.outputs_spin.value() == 2
    assert dialog.type_combo.itemData(dialog.type_combo.currentIndex()) == "MLP"

    # Simulate user changes
    dialog.name_edit.setText("CreatedGraph")
    dialog.inputs_spin.setValue(6)
    dialog.outputs_spin.setValue(3)
    dialog.type_combo.setCurrentIndex(1)  # ANFIS

    dialog._on_accept()

    created = vm.get_created_graph()
    assert created is not None
    assert created["name"] == "CreatedGraph"
    assert created["num_inputs"] == 6
    assert created["num_outputs"] == 3
    assert created["type"] == "ANFIS"
