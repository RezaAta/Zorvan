import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False


@pytest.mark.skipif(not PYQT, reason="PyQt6 not available")
def test_layouts_view_apply_calls_viewmodel():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from gui_framework.views.layouts_view import LayoutsView

    class MockVM:
        def __init__(self):
            self.calls = []

        def is_initialized(self):
            return True

        def apply_layout(self, algorithm, direction, spacing):
            self.calls.append((algorithm, direction, spacing))

    vm = MockVM()

    view = LayoutsView(vm)

    # Set algorithm to Grid (data 'grid') — find index
    for i in range(view.algo_combo.count()):
        if view.algo_combo.itemData(i) == "grid":
            view.algo_combo.setCurrentIndex(i)
            break

    # Set direction Top->Bottom (TB)
    for i in range(view.dir_combo.count()):
        if view.dir_combo.itemData(i) == "TB":
            view.dir_combo.setCurrentIndex(i)
            break

    # Set spacing
    view.spacing_spin.setValue(250)

    # Click apply
    view.apply_button.click()

    assert len(vm.calls) == 1
    algo, direction, spacing = vm.calls[0]
    assert algo == "grid"
    assert direction == "TB"
    assert spacing == 250
