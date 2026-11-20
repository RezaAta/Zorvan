"""
Tests for PlotConfigViewModel - Pure Python plot configuration logic.

Tests node selection, filtering, and configuration without PyQt.
"""

import pytest

from gui_framework.viewmodels.plot_config_viewmodel import NodeInfo, PlotConfigViewModel


class TestPlotConfigViewModelInitialization:
    """Test PlotConfigViewModel initialization."""

    def test_default_initialization(self):
        """Test default initialization."""
        vm = PlotConfigViewModel()

        assert vm.get_max_iterations() == 100
        assert vm.get_available_nodes() == []
        assert vm.get_selected_nodes() == []
        assert vm.get_filter() == "all"

    def test_custom_max_iterations(self):
        """Test initialization with custom max iterations."""
        vm = PlotConfigViewModel(max_iterations=500)

        assert vm.get_max_iterations() == 500


class TestPlotConfigViewModelNodeManagement:
    """Test node loading and management."""

    def test_load_nodes(self):
        """Test loading nodes."""
        vm = PlotConfigViewModel()

        nodes = [
            NodeInfo(name="A", node_id="A"),
            NodeInfo(name="B", node_id="B"),
            NodeInfo(name="C", node_id="C"),
        ]

        changes = []
        vm.observe_property("nodes_changed", lambda old, new: changes.append(new))

        vm.load_nodes(nodes)

        assert len(vm.get_available_nodes()) == 3
        assert len(changes) == 1

    def test_load_nodes_with_subgraphs(self):
        """Test loading nodes with subgraph information."""
        vm = PlotConfigViewModel()

        nodes = [
            NodeInfo(name="A", node_id="A"),
            NodeInfo(name="B", node_id="B", is_in_subgraph=True, subgraph_name="SG1"),
            NodeInfo(name="C", node_id="C", is_in_subgraph=True, subgraph_name="SG2"),
            NodeInfo(name="D", node_id="D", is_in_subgraph=True, subgraph_name="SG1"),
        ]

        vm.load_nodes(nodes)

        subgraphs = vm.get_subgraph_names()
        assert len(subgraphs) == 2
        assert "SG1" in subgraphs
        assert "SG2" in subgraphs


class TestPlotConfigViewModelSelection:
    """Test node selection management."""

    def test_select_node(self):
        """Test selecting a node."""
        vm = PlotConfigViewModel()
        vm.load_nodes([NodeInfo(name="A", node_id="A")])

        changes = []
        vm.observe_property("selection_changed", lambda old, new: changes.append(new))

        vm.select_node("A")

        assert vm.is_node_selected("A")
        assert len(changes) == 1

    def test_select_duplicate_node(self):
        """Test selecting already selected node."""
        vm = PlotConfigViewModel()
        vm.load_nodes([NodeInfo(name="A", node_id="A")])

        vm.select_node("A")

        changes = []
        vm.observe_property("selection_changed", lambda old, new: changes.append(new))

        vm.select_node("A")  # Duplicate

        assert len(changes) == 0  # No change

    def test_deselect_node(self):
        """Test deselecting a node."""
        vm = PlotConfigViewModel()
        vm.load_nodes([NodeInfo(name="A", node_id="A")])
        vm.select_node("A")

        vm.deselect_node("A")

        assert not vm.is_node_selected("A")

    def test_deselect_unselected_node(self):
        """Test deselecting unselected node is safe."""
        vm = PlotConfigViewModel()

        changes = []
        vm.observe_property("selection_changed", lambda old, new: changes.append(new))

        vm.deselect_node("A")  # Not selected

        assert len(changes) == 0

    def test_toggle_node(self):
        """Test toggling node selection."""
        vm = PlotConfigViewModel()
        vm.load_nodes([NodeInfo(name="A", node_id="A")])

        # Toggle on
        vm.toggle_node("A")
        assert vm.is_node_selected("A")

        # Toggle off
        vm.toggle_node("A")
        assert not vm.is_node_selected("A")

    def test_get_selected_nodes(self):
        """Test getting list of selected nodes."""
        vm = PlotConfigViewModel()
        vm.load_nodes(
            [
                NodeInfo(name="A", node_id="A"),
                NodeInfo(name="B", node_id="B"),
                NodeInfo(name="C", node_id="C"),
            ]
        )

        vm.select_node("B")
        vm.select_node("A")
        vm.select_node("C")

        selected = vm.get_selected_nodes()
        assert selected == ["A", "B", "C"]  # Sorted

    def test_select_all_visible(self):
        """Test selecting all visible nodes."""
        vm = PlotConfigViewModel()
        vm.load_nodes(
            [
                NodeInfo(name="A", node_id="A"),
                NodeInfo(name="B", node_id="B"),
                NodeInfo(name="C", node_id="C"),
            ]
        )

        vm.select_all_visible()

        assert vm.get_selection_count() == 3
        assert vm.is_node_selected("A")
        assert vm.is_node_selected("B")
        assert vm.is_node_selected("C")

    def test_deselect_all(self):
        """Test deselecting all nodes."""
        vm = PlotConfigViewModel()
        vm.load_nodes(
            [NodeInfo(name="A", node_id="A"), NodeInfo(name="B", node_id="B")]
        )
        vm.select_node("A")
        vm.select_node("B")

        vm.deselect_all()

        assert vm.get_selection_count() == 0
        assert not vm.is_node_selected("A")
        assert not vm.is_node_selected("B")

    def test_get_selection_count(self):
        """Test getting selection count."""
        vm = PlotConfigViewModel()
        vm.load_nodes(
            [NodeInfo(name="A", node_id="A"), NodeInfo(name="B", node_id="B")]
        )

        assert vm.get_selection_count() == 0

        vm.select_node("A")
        assert vm.get_selection_count() == 1

        vm.select_node("B")
        assert vm.get_selection_count() == 2

    def test_has_selection(self):
        """Test checking if any nodes are selected."""
        vm = PlotConfigViewModel()
        vm.load_nodes([NodeInfo(name="A", node_id="A")])

        assert not vm.has_selection()

        vm.select_node("A")
        assert vm.has_selection()


class TestPlotConfigViewModelFiltering:
    """Test node filtering."""

    def test_default_filter_all(self):
        """Test default filter shows all nodes."""
        vm = PlotConfigViewModel()
        nodes = [
            NodeInfo(name="A", node_id="A"),
            NodeInfo(name="B", node_id="B", is_in_subgraph=True, subgraph_name="SG1"),
        ]
        vm.load_nodes(nodes)

        filtered = vm.get_filtered_nodes()
        assert len(filtered) == 2

    def test_filter_mother_only(self):
        """Test mother graph filter."""
        vm = PlotConfigViewModel()
        nodes = [
            NodeInfo(name="A", node_id="A"),  # Mother only
            NodeInfo(name="B", node_id="B", is_in_subgraph=True, subgraph_name="SG1"),
            NodeInfo(name="C", node_id="C"),  # Mother only
        ]
        vm.load_nodes(nodes)

        vm.set_filter("mother")

        filtered = vm.get_filtered_nodes()
        assert len(filtered) == 2
        assert filtered[0].name == "A"
        assert filtered[1].name == "C"

    def test_filter_by_subgraph(self):
        """Test filtering by subgraph."""
        vm = PlotConfigViewModel()
        nodes = [
            NodeInfo(name="A", node_id="A"),
            NodeInfo(name="B", node_id="B", is_in_subgraph=True, subgraph_name="SG1"),
            NodeInfo(name="C", node_id="C", is_in_subgraph=True, subgraph_name="SG2"),
            NodeInfo(name="D", node_id="D", is_in_subgraph=True, subgraph_name="SG1"),
        ]
        vm.load_nodes(nodes)

        vm.set_filter("SG1")

        filtered = vm.get_filtered_nodes()
        assert len(filtered) == 2
        assert filtered[0].name == "B"
        assert filtered[1].name == "D"

    def test_set_filter_triggers_observable(self):
        """Test filter change triggers observable."""
        vm = PlotConfigViewModel()
        vm.load_nodes([NodeInfo(name="A", node_id="A")])

        changes = []
        vm.observe_property("filter_changed", lambda old, new: changes.append(new))

        vm.set_filter("mother")

        assert len(changes) == 1

    def test_set_same_filter_no_change(self):
        """Test setting same filter doesn't trigger observable."""
        vm = PlotConfigViewModel()
        vm.load_nodes([NodeInfo(name="A", node_id="A")])

        changes = []
        vm.observe_property("filter_changed", lambda old, new: changes.append(new))

        vm.set_filter("all")  # Already 'all'

        assert len(changes) == 0

    def test_select_all_visible_respects_filter(self):
        """Test select all visible only selects filtered nodes."""
        vm = PlotConfigViewModel()
        nodes = [
            NodeInfo(name="A", node_id="A"),
            NodeInfo(name="B", node_id="B", is_in_subgraph=True, subgraph_name="SG1"),
            NodeInfo(name="C", node_id="C"),
        ]
        vm.load_nodes(nodes)

        vm.set_filter("mother")  # Only A and C visible
        vm.select_all_visible()

        assert vm.is_node_selected("A")
        assert not vm.is_node_selected("B")  # Not visible
        assert vm.is_node_selected("C")

    def test_get_filter_options(self):
        """Test getting available filter options."""
        vm = PlotConfigViewModel()
        nodes = [
            NodeInfo(name="A", node_id="A"),
            NodeInfo(name="B", node_id="B", is_in_subgraph=True, subgraph_name="SG1"),
            NodeInfo(name="C", node_id="C", is_in_subgraph=True, subgraph_name="SG2"),
        ]
        vm.load_nodes(nodes)

        options = vm.get_filter_options()

        assert options == ["all", "mother", "SG1", "SG2"]


class TestPlotConfigViewModelMaxIterations:
    """Test max iterations configuration."""

    def test_set_max_iterations(self):
        """Test setting max iterations."""
        vm = PlotConfigViewModel()

        vm.set_max_iterations(1000)

        assert vm.get_max_iterations() == 1000

    def test_set_max_iterations_minimum(self):
        """Test max iterations minimum enforced."""
        vm = PlotConfigViewModel()

        vm.set_max_iterations(5)

        assert vm.get_max_iterations() == 10  # Minimum


class TestPlotConfigViewModelObservableProperties:
    """Test observable property notifications."""

    def test_nodes_changed_observable(self):
        """Test nodes_changed triggers observers."""
        vm = PlotConfigViewModel()

        observed = []
        vm.observe_property("nodes_changed", lambda old, new: observed.append(new))

        vm.load_nodes([NodeInfo(name="A", node_id="A")])

        assert len(observed) == 1

    def test_selection_changed_observable(self):
        """Test selection_changed triggers observers."""
        vm = PlotConfigViewModel()
        vm.load_nodes(
            [NodeInfo(name="A", node_id="A"), NodeInfo(name="B", node_id="B")]
        )

        observed = []
        vm.observe_property("selection_changed", lambda old, new: observed.append(new))

        vm.select_node("A")
        vm.select_node("B")
        vm.deselect_node("A")

        assert len(observed) == 3

    def test_filter_changed_observable(self):
        """Test filter_changed triggers observers."""
        vm = PlotConfigViewModel()
        vm.load_nodes([NodeInfo(name="A", node_id="A")])

        observed = []
        vm.observe_property("filter_changed", lambda old, new: observed.append(new))

        vm.set_filter("mother")

        assert len(observed) == 1
