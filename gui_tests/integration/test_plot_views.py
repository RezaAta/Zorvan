"""
Integration tests for Plot Views (headless mode).

Tests the plot view components without requiring a display.
Uses QT_QPA_PLATFORM=offscreen for headless testing.
"""

import os

import pytest

# Set up headless mode before importing PyQt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication, QDialog

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from gui_framework.viewmodels.plot_config_viewmodel import (
        NodeInfo,
        PlotConfigViewModel,
    )
    from gui_framework.viewmodels.plot_viewmodel import PlotDataPoint, PlotViewModel
    from gui_framework.views.plot_config_view import PlotConfigView
    from gui_framework.views.plot_view import PlotView


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    if PYQT_AVAILABLE:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    else:
        yield None


class TestPlotConfigViewIntegration:
    """Integration tests for PlotConfigView."""

    def test_plot_config_view_creation(self, qapp):
        """Test creating a plot config view."""
        vm = PlotConfigViewModel(max_iterations=100)

        # Load some test nodes
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
        """Test filter combo box population."""
        vm = PlotConfigViewModel()

        # Load nodes with subgraph
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

        # Check filter combo has expected items
        assert view.filter_combo.count() >= 3  # All, Mother, SubGraph1

    def test_plot_config_node_selection(self, qapp):
        """Test node selection via UI."""
        vm = PlotConfigViewModel()

        nodes = [
            NodeInfo(name="A", node_id="node_a"),
            NodeInfo(name="B", node_id="node_b"),
        ]
        vm.load_nodes(nodes)

        view = PlotConfigView(vm)

        # Select first node via ViewModel
        vm.select_node("A")

        # Check UI reflects selection
        assert vm.get_selection_count() == 1
        assert "A" in vm.get_selected_nodes()

    def test_plot_config_select_all(self, qapp):
        """Test select all functionality."""
        vm = PlotConfigViewModel()

        nodes = [NodeInfo(name=f"Node{i}", node_id=f"node_{i}") for i in range(5)]
        vm.load_nodes(nodes)

        view = PlotConfigView(vm)

        # Click select all button
        view._on_select_all()

        # Check all visible nodes are selected
        assert vm.get_selection_count() == 5

    def test_plot_config_max_iterations(self, qapp):
        """Test max iterations setting."""
        vm = PlotConfigViewModel(max_iterations=100)
        view = PlotConfigView(vm)

        # Check initial value
        assert view.max_iter_spin.value() == 100

        # Change via UI
        view.max_iter_spin.setValue(500)

        # Check ViewModel updated
        assert vm.get_max_iterations() == 500


class TestPlotViewIntegration:
    """Integration tests for PlotView."""

    def test_plot_view_creation_matplotlib(self, qapp):
        """Test creating a plot view with matplotlib backend."""
        try:
            import matplotlib

            vm = PlotViewModel(max_iterations=100, backend="matplotlib")
            view = PlotView(vm)

            assert view is not None
            assert view.viewmodel == vm
        except ImportError:
            pytest.skip("Matplotlib not available")

    def test_plot_view_creation_pyqtgraph(self, qapp):
        """Test creating a plot view with pyqtgraph backend."""
        try:
            import pyqtgraph

            vm = PlotViewModel(max_iterations=100, backend="pyqtgraph")
            view = PlotView(vm)

            assert view is not None
            assert view.viewmodel == vm
        except ImportError:
            pytest.skip("PyQtGraph not available")

    def test_plot_view_add_nodes(self, qapp):
        """Test adding nodes to plot."""
        vm = PlotViewModel(max_iterations=100, backend="matplotlib")
        vm.add_node("A")
        vm.add_node("B")

        view = PlotView(vm)

        # Check nodes appear in list
        assert view.node_list_widget.count() == 2

    def test_plot_view_add_data(self, qapp):
        """Test adding data points."""
        vm = PlotViewModel(max_iterations=100, backend="matplotlib")
        vm.add_node("A")

        view = PlotView(vm)

        # Add some data points
        for i in range(10):
            vm.add_data_point("A", float(i * 2), iteration=i)

        # Check data is stored
        data = vm.get_plot_data("A")
        assert len(data) == 10
        assert data[0].iteration == 0
        assert data[0].value == 0.0

    def test_plot_view_clear(self, qapp):
        """Test clearing plot data."""
        vm = PlotViewModel(max_iterations=100, backend="matplotlib")
        vm.add_node("A")

        # Add data
        for i in range(10):
            vm.add_data_point("A", float(i), iteration=i)

        view = PlotView(vm)

        # Clear via button
        view._on_clear_clicked()

        # Check data cleared
        data = vm.get_plot_data("A")
        assert len(data) == 0

    def test_plot_view_remove_node(self, qapp):
        """Test removing a node from plot."""
        vm = PlotViewModel(max_iterations=100, backend="matplotlib")
        vm.add_node("A")
        vm.add_node("B")

        view = PlotView(vm)

        # Select first item
        view.node_list_widget.setCurrentRow(0)

        # Remove via button
        view._on_remove_node_clicked()

        # Check node removed
        assert len(vm.get_plotted_nodes()) == 1

    def test_plot_view_backend_switching(self, qapp):
        """Test switching between backends."""
        try:
            import matplotlib
            import pyqtgraph

            vm = PlotViewModel(max_iterations=100, backend="matplotlib")
            view = PlotView(vm)

            # Switch to pyqtgraph
            vm.set_backend("pyqtgraph")

            # Check backend updated
            assert vm.get_backend() == "pyqtgraph"

        except ImportError:
            pytest.skip("Matplotlib or PyQtGraph not available")


class TestPlotViewsDataFlow:
    """Test data flow between config and plot views."""

    def test_config_to_plot_workflow(self, qapp):
        """Test typical workflow: config -> plot."""
        # Step 1: Configure plot
        config_vm = PlotConfigViewModel(max_iterations=100)

        nodes = [
            NodeInfo(name="A", node_id="node_a"),
            NodeInfo(name="B", node_id="node_b"),
            NodeInfo(name="C", node_id="node_c"),
        ]
        config_vm.load_nodes(nodes)

        # Select some nodes
        config_vm.select_node("A")
        config_vm.select_node("B")

        config_view = PlotConfigView(config_vm)

        # Step 2: Create plot with selected nodes
        selected_nodes = config_vm.get_selected_nodes()
        max_iter = config_vm.get_max_iterations()

        plot_vm = PlotViewModel(max_iterations=max_iter, backend="matplotlib")
        plot_vm.set_nodes(selected_nodes)

        plot_view = PlotView(plot_vm)

        # Verify configuration transferred
        assert plot_vm.get_max_iterations() == 100
        assert len(plot_vm.get_plotted_nodes()) == 2
        assert "A" in plot_vm.get_plotted_nodes()
        assert "B" in plot_vm.get_plotted_nodes()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
