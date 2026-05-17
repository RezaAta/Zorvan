from gui_framework.viewmodels.dialogs.learning_rate_viewmodel import (
    LearningRateViewModel,
)


def test_learning_rate_vm_basic():
    vm = LearningRateViewModel(0.05)
    vm.initialize()
    assert vm.get_value() == 0.05

    vm.set_value(0.1)
    assert vm.get_value() == 0.1

    vm.create_snapshot()
    vm.set_value(0.2)
    vm.reset_to_snapshot()
    assert vm.get_value() == 0.1

    class Dummy:
        def __init__(self):
            self.value = 0.0

    d = Dummy()
    vm.set_value(0.42)
    assert vm.apply_to_node(d)
    assert d.value == 0.42
