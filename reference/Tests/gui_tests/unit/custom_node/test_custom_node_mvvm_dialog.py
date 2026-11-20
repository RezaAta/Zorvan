import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.viewmodels.dialogs.custom_node_viewmodel import CustomNodeViewModel
from gui_framework.views.dialogs.custom_node_dialog import CustomNodeDialog


def test_mvvm_dialog_saves_definition(monkeypatch):
    app = QApplication.instance() or QApplication([])

    # Track if add_definition is called with expected type
    called = {"ok": False, "definition": None}

    class StubManager:
        def add_definition(self, definition):
            called["ok"] = True
            called["definition"] = definition
            return True

    # Patch the accessor used by CustomNodeViewModel.save_definition()
    try:
        import gui_framework.legacy as legacy_mod

        monkeypatch.setattr(
            legacy_mod, "get_custom_node_manager_safe", lambda: StubManager()
        )
    except Exception:
        pytest.skip("custom_node_manager not available to patch")

    vm = CustomNodeViewModel()
    vm.set_type_name("MyCustom")
    vm.set_input_count(2)
    vm.set_batch_size(2)
    vm.set_description("A test node")
    vm.set_operation_code("return input1 + input2")

    dlg = CustomNodeDialog(vm)

    # Fill UI fields as user would
    dlg.type_name_edit.setText("MyCustom")
    dlg.description_edit.setText("A test node")
    dlg.input_count_spin.setValue(2)
    dlg.batch_size_spin.setValue(2)
    dlg.operation_edit.setPlainText("return input1 + input2")

    # Click save
    dlg._on_save()

    assert called["ok"] is True
    assert hasattr(called["definition"], "type_name")
    assert called["definition"].type_name == "MyCustom"
