"""Unit tests for the PyQt6 PlotView that binds to PlotViewModel.

Requires PyQt6; tests are skipped if PyQt6 is not available.
"""

from pathlib import Path

import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")

from gui_framework.viewmodels.plot_viewmodel import PlotViewModel
from zorvan.GUI.plot_view import PlotView


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_plot_view_initializes_and_displays_nodes(qapp):
    vm = PlotViewModel()
    vm.add_node("A")
    vm.add_node("B")

    view = PlotView(vm)

    # Lines should exist for both nodes
    assert "A" in view._lines
    assert "B" in view._lines

    # Initial plot has no data
    for name in ("A", "B"):
        line = view._lines[name]
        xs = line.get_xdata()
        ys = line.get_ydata()
        assert len(xs) == 0
        assert len(ys) == 0

    view.cleanup()


def test_plot_view_updates_on_data(qapp):
    vm = PlotViewModel()
    vm.add_node("A")
    view = PlotView(vm)

    # Add a data point and ensure it appears on the line
    vm.add_data_point("A", 3.14, iteration=1)

    # Force update
    view.update_plot()

    line = view._lines["A"]
    xs = line.get_xdata()
    ys = line.get_ydata()

    assert list(xs) == [1]
    assert list(ys) == [3.14]

    view.cleanup()
