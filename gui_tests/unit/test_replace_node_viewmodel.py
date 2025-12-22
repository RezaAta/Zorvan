import pytest

from gui_framework.viewmodels.dialogs.replace_node_viewmodel import ReplaceNodeViewModel


def sample_registry():
    return {
        "Basic": {
            "description": "Basic nodes",
            "nodes": [
                ("AdditionNode", "Addition", "Adds"),
                ("MultiplicationNode", "Multiplication", "Multiply"),
            ],
        },
        "Activation": {
            "description": "Activation nodes",
            "nodes": [("SigmoidNode", "Sigmoid", "Sigmoid activation")],
        },
    }


def test_filtering_and_selection():
    vm = ReplaceNodeViewModel(sample_registry())
    vm.initialize()
    # initial list contains all
    all_filtered = vm.get_filtered()
    assert any(t == "AdditionNode" for _, t, *_ in all_filtered)

    vm.set_search_text("sigmoid")
    filtered = vm.get_filtered()
    assert len(filtered) == 1
    assert filtered[0][1] == "SigmoidNode"
    assert vm.select_type("SigmoidNode")
    assert not vm.select_type("NonExistentNode")
