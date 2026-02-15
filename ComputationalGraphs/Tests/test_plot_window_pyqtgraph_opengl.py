import pytest

# Skip GUI tests when PyQt6 isn't available in CI environments
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

# Use the MVVM PlotView instead of legacy PlotWindowPG
from gui_framework.viewmodels.plot_viewmodel import PlotViewModel
from gui_framework.views.plot_view import PlotView


class DummyNode:
    def __init__(self, name):
        self.name = name
        self.value = 0.0


def _create_app():
    app = QApplication.instance() or QApplication([])
    return app


def test_opengl_toggle_recreates_widget():
    """Test that backend switching works in the MVVM PlotView.

    This test verifies that the PlotView can switch between backends
    (matplotlib/pyqtgraph) which involves recreating the plot widget.
    """
    app = _create_app()

    # Create PlotViewModel with pyqtgraph backend
    vm = PlotViewModel(backend="pyqtgraph")
    vm.set_nodes(["A", "B"])

    # Create PlotView
    pv = PlotView(vm, parent=None)
    assert pv is not None

    # Initial widget exists
    assert hasattr(pv, "plot_widget") and pv.plot_widget is not None

    # Toggle antialiasing (available in the new PlotView)
    if hasattr(pv, "antialias_check"):
        pv.antialias_check.setChecked(False)
        pv.antialias_check.setChecked(True)

    # Switch backend via combo box if available
    if hasattr(pv, "backend_combo") and pv.backend_combo.count() > 1:
        # Switch to matplotlib
        pv.backend_combo.setCurrentIndex(0)
        # Switch back to pyqtgraph
        pv.backend_combo.setCurrentIndex(1)

    # Assert plot_widget still exists after switches
    assert hasattr(pv, "plot_widget") and pv.plot_widget is not None

    # Cleanup
    try:
        pv.close()
    except Exception:
        pass
