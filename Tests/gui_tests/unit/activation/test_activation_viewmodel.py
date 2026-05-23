from gui_framework.viewmodels.dialogs.activation_viewmodel import ActivationViewModel


def test_activation_vm_basic():
    vm = ActivationViewModel()
    vm.initialize()
    assert "Sigmoid" in vm.get_available()
    assert vm.get_selected() is None

    vm.set_selected("ReLU")
    assert vm.get_selected() == "ReLU"

    vm.set_selected("NonExistent")
    assert vm.get_selected() == "ReLU"  # unchanged
