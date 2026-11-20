"""Integration tests for the PlotConfigView dialog."""

import os

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from gui_framework.viewmodels.plot_config_viewmodel import (
        NodeInfo,
        PlotConfigViewModel,
    )
    from gui_framework.views.plot_config_view import PlotConfigView


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


class TestPlotConfigViewIntegration:
    def test_plot_config_view_creation(self, qapp):
        vm = PlotConfigViewModel(max_iterations=100)
        nodes = [
            NodeInfo(name="A", node_id="node_a"),
            NodeInfo(name="B", node_id="node_b"),
            NodeInfo(name="C", node_id="node_c"),
        ]
        vm.load_nodes(nodes)

        view = PlotConfigView(vm)
        assert view is not None
        assert view.viewmodel == vm

    def test_plot_config_filter_combo(self, qapp):
        vm = PlotConfigViewModel()
        nodes = [
            NodeInfo(name="A", node_id="node_a", is_in_subgraph=False),
            NodeInfo(
                name="B",
                node_id="node_b",
                is_in_subgraph=True,
                subgraph_name="SubGraph1",
            ),
            NodeInfo(
                name="C",
                node_id="node_c",
                is_in_subgraph=True,
                subgraph_name="SubGraph1",
            ),
        ]
        vm.load_nodes(nodes)

        view = PlotConfigView(vm)
        assert view.filter_combo.count() >= 3

    def test_plot_config_node_selection(self, qapp):
        vm = PlotConfigViewModel()
        nodes = [
            NodeInfo(name="A", node_id="node_a"),
            NodeInfo(name="B", node_id="node_b"),
        ]
        vm.load_nodes(nodes)

        view = PlotConfigView(vm)
        vm.select_node("A")

        assert vm.get_selection_count() == 1
        assert "A" in vm.get_selected_nodes()

    def test_plot_config_select_all(self, qapp):
        vm = PlotConfigViewModel()
        nodes = [NodeInfo(name=f"Node{i}", node_id=f"node_{i}") for i in range(5)]
        vm.load_nodes(nodes)

        view = PlotConfigView(vm)
        view._on_select_all()

        assert vm.get_selection_count() == 5

    def test_plot_config_max_iterations(self, qapp):
        vm = PlotConfigViewModel(max_iterations=100)
        view = PlotConfigView(vm)

        assert view.max_iter_spin.value() == 100
        view.max_iter_spin.setValue(500)

        assert vm.get_max_iterations() == 500
