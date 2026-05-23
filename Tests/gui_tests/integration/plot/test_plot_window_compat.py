"""Integration tests for plot window compatibility and label deduplication."""

import os

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from zorvan.GUI.plot_window import PlotWindow
    from zorvan.Nodes.DataStreamNode import DataStreamNode


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    if PYQT_AVAILABLE:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    else:
        yield None


def test_plot_window_compat_duplicate_name_labels(qapp):
    n1 = DataStreamNode("same")
    n2 = DataStreamNode("same")
    n3 = DataStreamNode("same")

    pw = PlotWindow([n1, n2, n3], max_iterations=50)
    if not pw._adapter or pw._adapter.plot_viewmodel is None:
        pw.close()
        pytest.skip("PlotAdapter failed to create view in this environment")

    plotted = pw._adapter.plot_viewmodel.get_plotted_nodes()
    assert len(plotted) == 3
    assert len(set(plotted)) == 3
    assert any("same (" in lbl for lbl in plotted)
    pw.close()
