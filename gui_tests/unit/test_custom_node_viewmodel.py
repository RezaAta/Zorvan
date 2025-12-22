import pytest

from gui_framework.viewmodels.dialogs.custom_node_viewmodel import CustomNodeViewModel


class DummyNode:
    def __init__(self):
        self.name = "MyNode"
        self.description = "A test node"
        self.params = {"alpha": 1.0, "beta": "x"}


def test_load_and_apply():
    node = DummyNode()
    vm = CustomNodeViewModel()
    vm.load_from_node(node)

    assert vm.get_name() == "MyNode"
    assert vm.get_description() == "A test node"
    ps = vm.get_params()
    assert ps["alpha"] == 1.0

    vm.set_param("alpha", 2.5)
    assert vm.get_params()["alpha"] == 2.5

    vm.set_name("NewName")
    vm.set_description("Changed")

    ok = vm.apply_to_node()
    assert ok
    assert node.name == "NewName"
    assert node.description == "Changed"
    assert node.params["alpha"] == 2.5
