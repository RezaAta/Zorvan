"""
Unit tests for PlotAdapter: ensure plot window creation, data update, and closing work.
"""

import os

import pytest

# Headless mode for tests
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from gui_framework.adapters.plot_adapter import PlotAdapter


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class DummyNode:
    def __init__(self, name):
        self.name = name
        self.value = 0.0


def test_plot_adapter_create_and_update(qapp):
    adapter = PlotAdapter(parent=None)

    # Create plot window for nodes
    nodes = ["A", "B"]
    adapter._create_plot_window(nodes, max_iterations=100)

    assert adapter.is_plot_window_open()

    # Simulate updates
    adapter.update_plot("A", 1.23, iteration=1)
    adapter.update_plot("B", 2.34, iteration=1)

    # Verify plotted nodes are present
    plotted = adapter.get_plotted_nodes()
    assert "A" in plotted
    assert "B" in plotted

    # Close plot
    adapter.close_plot_window()
    assert not adapter.is_plot_window_open()


def test_plot_adapter_batch_updates(qapp):
    adapter = PlotAdapter(parent=None)
    nodes = ["X", "Y", "Z"]
    adapter._create_plot_window(nodes, max_iterations=50)

    data = {"X": 1.0, "Y": 2.0, "Z": 3.0}
    adapter.update_plots_batch(data, iteration=5)

    # Ensure nodes still present
    assert set(adapter.get_plotted_nodes()) == set(nodes)

    adapter.close_plot_window()
