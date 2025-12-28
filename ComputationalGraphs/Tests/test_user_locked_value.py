from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from ComputationalGraphs.Nodes.BasicNode import BasicNode
from gui_framework.viewmodels.dialogs.node_editor_viewmodel import NodeEditorViewModel


class DummyNode(BasicNode):
    def __init__(self, name, value=0):
        super().__init__(name, value)

    def Operation(self, inputs):
        return 0

    def IsValidInput(self, inp):
        return True


def test_apply_to_node_locks_value_and_persists_after_graph_reset():
    node = DummyNode("test", value=0)

    # NodeEditorViewModel is abstract (lifecycle methods); use a small concrete subclass for testing
    class TestNodeEditorViewModel(NodeEditorViewModel):
        def initialize(self):
            pass

        def cleanup(self):
            pass

    vm = TestNodeEditorViewModel()
    vm.load_from_node(node)

    vm.set_value("42")
    assert vm.get_value() == "42"

    assert vm.apply_to_node() is True
    assert node.value == 42
    assert getattr(node, "user_locked_value", False) is True

    g = Graph()
    g.nodes = [node]
    g.ResetNodeValues()

    # Value should persist because it's user-locked
    assert node.value == 42


def test_forward_reset_skips_user_locked_values():
    node_locked = DummyNode("n_locked", value=5)
    node_locked.user_locked_value = True

    node_unlocked = DummyNode("n_unlocked", value=7)
    node_unlocked.user_locked_value = False

    mlp = MLPGraphForwardProcessing(1, 1, 0)
    mlp.nodes = [node_locked, node_unlocked]

    mlp.ResetNetwork()

    # Locked value should remain
    assert node_locked.value == 5
    # Unlocked should be reset to 0.0
    assert node_unlocked.value == 0.0
