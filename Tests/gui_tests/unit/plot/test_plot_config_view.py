"""Unit tests for PlotConfigView (PyQt6 dialog) binding to PlotConfigViewModel."""

import pytest
from PyQt6.QtCore import Qt

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")

from gui_framework.viewmodels.plot_config_viewmodel import NodeInfo, PlotConfigViewModel
from gui_framework.views.plot_config_view import PlotConfigView


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_plot_config_view_initial_population(qapp):
    vm = PlotConfigViewModel()
    nodes = [NodeInfo(name=f"N{i}", node_id=f"n{i}") for i in range(5)]
    vm.load_nodes(nodes)

    view = PlotConfigView(vm)
    # Process pending bindings
    QApplication.processEvents()

    # Node list should have 5 items
    assert view.node_list.count() == 5
    # Selection label should reflect 0 selected
    assert "Selected: 0" in view.selection_label.text()

    view.close()


def test_select_all_and_none_buttons(qapp):
    vm = PlotConfigViewModel()
    nodes = [NodeInfo(name=f"A{i}", node_id=f"a{i}") for i in range(3)]
    vm.load_nodes(nodes)

    view = PlotConfigView(vm)
    QApplication.processEvents()

    # Click select all
    view.select_all_button.click()
    QApplication.processEvents()

    assert set(vm.get_selected_nodes()) == set(n.name for n in nodes)
    assert "Selected: 3" in view.selection_label.text()

    # Click select none
    view.select_none_button.click()
    QApplication.processEvents()

    assert vm.get_selected_nodes() == []
    assert "Selected: 0" in view.selection_label.text()

    view.close()


def test_filter_changes_populate_visible_nodes(qapp):
    vm = PlotConfigViewModel()
    nodes = [
        NodeInfo(name="A", node_id="a", is_in_subgraph=False),
        NodeInfo(name="B", node_id="b", is_in_subgraph=True, subgraph_name="S1"),
        NodeInfo(name="C", node_id="c", is_in_subgraph=True, subgraph_name="S1"),
    ]
    vm.load_nodes(nodes)

    view = PlotConfigView(vm)
    QApplication.processEvents()

    # Default filter 'all' shows 3 nodes
    assert view.node_list.count() == 3

    # Change filter to 'Mother' (index 1)
    view.filter_combo.setCurrentIndex(1)
    QApplication.processEvents()

    # Now only mother nodes should be visible
    assert view.node_list.count() == 1
    assert view.node_list.item(0).text() == "A"

    view.close()
