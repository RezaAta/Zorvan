from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel


class Dummy:
    def __init__(self):
        self.name = "D"
        self.value = 0


def test_set_value_marks_node_locked():
    node = Dummy()
    vm = NodeEditorViewModel(node)
    vm.initialize()

    ok = vm.set_value("42")
    assert ok
    assert node.value == 42
    assert getattr(node, "user_locked_value", False) is True

    # Clearing value unlocks
    ok = vm.set_value("")
    assert ok
    assert getattr(node, "user_locked_value", False) is False
