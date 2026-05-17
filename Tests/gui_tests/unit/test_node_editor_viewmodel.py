from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel


class X:
    def __init__(self):
        self.name = "X"
        self.value = 42
        self.flag = True


def test_load_and_edit_node_properties():
    x = X()
    vm = NodeEditorViewModel(x)
    vm.initialize()

    props = vm.get_properties()
    assert props["name"] == "X"
    assert props["value"] == 42

    ok = vm.set_property("value", 100)
    assert ok
    assert x.value == 100
    assert vm.get_properties()["value"] == 100
