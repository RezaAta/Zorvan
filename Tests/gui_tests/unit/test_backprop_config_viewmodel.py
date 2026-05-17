from gui_framework.viewmodels.dialogs.backprop_config_viewmodel import (
    BackpropConfigViewModel,
)


def test_backprop_config_viewmodel_basic():
    vm = BackpropConfigViewModel(learning_rate=0.02, use_forward=True)
    assert vm.get_learning_rate() == 0.02
    assert vm.get_use_forward() is True

    vm.set_learning_rate(0.05)
    assert vm.get_learning_rate() == 0.05

    vm.create_snapshot()
    vm.set_learning_rate(0.1)
    vm.set_use_forward(False)
    vm.reset_to_snapshot()
    assert vm.get_learning_rate() == 0.05
    assert vm.get_use_forward() is True
