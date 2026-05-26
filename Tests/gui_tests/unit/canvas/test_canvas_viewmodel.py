"""
Unit tests for CanvasViewModel.

Tests the pure Python logic for canvas rendering state management
without requiring PyQt or a GUI.
"""

from unittest.mock import Mock

import pytest

from gui_framework.viewmodels.canvas_viewmodel import (
    CanvasViewModel,
    CanvasViewport,
    EdgeRenderState,
    NodeRenderState,
)


class MockNode:
    """Mock computational graph node for testing."""

    def __init__(self, name, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y
        self.predecessors = []


class MockGraph:
    """Mock computational graph for testing."""

    def __init__(self):
        self.nodes = []


@pytest.fixture
def viewmodel():
    """Create a fresh CanvasViewModel for each test."""
    vm = CanvasViewModel()
    vm.initialize()
    return vm


@pytest.fixture
def simple_graph():
    """Create a simple graph with 3 nodes and 2 edges."""
    graph = MockGraph()

    node_a = MockNode("A", 0, 0)
    node_b = MockNode("B", 100, 0)
    node_c = MockNode("C", 50, 100)

    node_b.predecessors = [node_a]
    node_c.predecessors = [node_a, node_b]

    graph.nodes = [node_a, node_b, node_c]
    return graph


class TestCanvasViewport:
    """Test viewport zoom/pan functionality."""

    def test_default_viewport(self):
        """Test default viewport state."""
        vp = CanvasViewport()
        assert vp.center_x == 0.0
        assert vp.center_y == 0.0
        assert vp.zoom_level == 1.0

    def test_zoom_in(self):
        """Test zooming in."""
        vp = CanvasViewport()
        vp.zoom_in(1.5)
        assert vp.zoom_level == 1.5

        vp.zoom_in(2.0)
        assert vp.zoom_level == 3.0

    def test_zoom_out(self):
        """Test zooming out."""
        vp = CanvasViewport()
        vp.zoom_out(2.0)
        assert vp.zoom_level == 0.5

        vp.zoom_out(2.0)
        assert vp.zoom_level == 0.25

    def test_zoom_limits(self):
        """Test zoom level limits."""
        vp = CanvasViewport(min_zoom=0.1, max_zoom=5.0)

        # Zoom out below minimum
        for _ in range(20):
            vp.zoom_out(1.5)
        assert vp.zoom_level >= vp.min_zoom

        # Zoom in above maximum
        vp.reset()
        for _ in range(20):
            vp.zoom_in(1.5)
        assert vp.zoom_level <= vp.max_zoom

    def test_pan(self):
        """Test panning."""
        vp = CanvasViewport()
        vp.pan(10, 20)
        assert vp.center_x == 10.0
        assert vp.center_y == 20.0

        vp.pan(-5, -10)
        assert vp.center_x == 5.0
        assert vp.center_y == 10.0

    def test_reset(self):
        """Test viewport reset."""
        vp = CanvasViewport()
        vp.zoom_in(2.0)
        vp.pan(50, 100)

        vp.reset()
        assert vp.center_x == 0.0
        assert vp.center_y == 0.0
        assert vp.zoom_level == 1.0


class TestCanvasViewModelInit:
    """Test CanvasViewModel initialization."""

    def test_initialization(self, viewmodel):
        """Test basic initialization."""
        assert viewmodel.get_node_count() == 0
        assert viewmodel.get_edge_count() == 0
        assert viewmodel.get_viewport() is not None

    def test_cleanup(self, viewmodel, simple_graph):
        """Test cleanup clears state."""
        viewmodel.load_graph(simple_graph)
        assert viewmodel.get_node_count() == 3

        viewmodel.cleanup()
        assert viewmodel.get_node_count() == 0
        assert viewmodel.get_edge_count() == 0


class TestGraphLoading:
    """Test loading graphs into the canvas."""

    def test_load_simple_graph(self, viewmodel, simple_graph):
        """Test loading a simple graph."""
        viewmodel.load_graph(simple_graph)

        assert viewmodel.get_node_count() == 3
        assert viewmodel.get_edge_count() == 3  # A->B, A->C, B->C

        # Check nodes exist
        assert viewmodel.get_node("A") is not None
        assert viewmodel.get_node("B") is not None
        assert viewmodel.get_node("C") is not None

    def test_node_positions_preserved(self, viewmodel, simple_graph):
        """Test that node positions are loaded correctly."""
        viewmodel.load_graph(simple_graph)

        node_a = viewmodel.get_node("A")
        assert node_a.x == 0
        assert node_a.y == 0

        node_b = viewmodel.get_node("B")
        assert node_b.x == 100
        assert node_b.y == 0

        node_c = viewmodel.get_node("C")
        assert node_c.x == 50
        assert node_c.y == 100

    def test_get_nodes_returns_list(self, viewmodel, simple_graph):
        """Test get_nodes returns all nodes."""
        viewmodel.load_graph(simple_graph)
        nodes = viewmodel.get_nodes()

        assert len(nodes) == 3
        assert all(isinstance(n, NodeRenderState) for n in nodes)

    def test_get_edges_returns_list(self, viewmodel, simple_graph):
        """Test get_edges returns all edges."""
        viewmodel.load_graph(simple_graph)
        edges = viewmodel.get_edges()

        assert len(edges) == 3
        assert all(isinstance(e, EdgeRenderState) for e in edges)


class TestViewportManagement:
    """Test viewport zoom/pan through ViewModel."""

    def test_zoom_in(self, viewmodel):
        """Test zoom in updates viewport."""
        initial_zoom = viewmodel.get_viewport().zoom_level
        viewmodel.zoom_in(1.5)

        assert viewmodel.get_viewport().zoom_level == initial_zoom * 1.5

    def test_zoom_out(self, viewmodel):
        """Test zoom out updates viewport."""
        initial_zoom = viewmodel.get_viewport().zoom_level
        viewmodel.zoom_out(2.0)

        assert viewmodel.get_viewport().zoom_level == initial_zoom / 2.0

    def test_pan(self, viewmodel):
        """Test pan updates viewport."""
        viewmodel.pan(50, 100)
        vp = viewmodel.get_viewport()

        assert vp.center_x == 50
        assert vp.center_y == 100

    def test_reset_viewport(self, viewmodel):
        """Test reset viewport."""
        viewmodel.zoom_in(2.0)
        viewmodel.pan(100, 200)

        viewmodel.reset_viewport()
        vp = viewmodel.get_viewport()

        assert vp.center_x == 0
        assert vp.center_y == 0
        assert vp.zoom_level == 1.0

    def test_viewport_changed_observable(self, viewmodel):
        """Test viewport_changed property triggers on changes."""
        initial_value = viewmodel.viewport_changed

        viewmodel.zoom_in()
        assert viewmodel.viewport_changed > initial_value

        viewmodel.pan(10, 20)
        assert viewmodel.viewport_changed > initial_value + 1


class TestNodePositions:
    """Test node position management."""

    def test_update_node_position(self, viewmodel, simple_graph):
        """Test updating a single node position."""
        viewmodel.load_graph(simple_graph)

        viewmodel.update_node_position("A", 200, 300)
        node = viewmodel.get_node("A")

        assert node.x == 200
        assert node.y == 300

    def test_update_multiple_positions(self, viewmodel, simple_graph):
        """Test updating multiple node positions at once."""
        viewmodel.load_graph(simple_graph)

        positions = {"A": (10, 20), "B": (30, 40), "C": (50, 60)}
        viewmodel.update_node_positions(positions)

        assert viewmodel.get_node("A").x == 10
        assert viewmodel.get_node("A").y == 20
        assert viewmodel.get_node("B").x == 30
        assert viewmodel.get_node("B").y == 40
        assert viewmodel.get_node("C").x == 50
        assert viewmodel.get_node("C").y == 60

    def test_nodes_changed_observable(self, viewmodel, simple_graph):
        """Test nodes_changed property triggers on position updates."""
        viewmodel.load_graph(simple_graph)
        initial_value = viewmodel.nodes_changed

        viewmodel.update_node_position("A", 100, 200)
        assert viewmodel.nodes_changed > initial_value


class TestNodeColors:
    """Test node color management for visualization."""

    def test_set_node_color(self, viewmodel, simple_graph):
        """Test setting a node color."""
        viewmodel.load_graph(simple_graph)

        viewmodel.set_node_color("A", "#FF0000")
        node = viewmodel.get_node("A")

        assert node.color == "#FF0000"

    def test_clear_node_colors(self, viewmodel, simple_graph):
        """Test clearing all node colors."""
        viewmodel.load_graph(simple_graph)

        viewmodel.set_node_color("A", "#FF0000")
        viewmodel.set_node_color("B", "#00FF00")

        viewmodel.clear_node_colors()

        assert viewmodel.get_node("A").color is None
        assert viewmodel.get_node("B").color is None


class TestActiveNodes:
    """Test active node tracking for Forward Processing."""

    def test_set_node_active(self, viewmodel, simple_graph):
        """Test marking a node as active."""
        viewmodel.load_graph(simple_graph)

        viewmodel.set_node_active("A", True)
        node = viewmodel.get_node("A")

        assert node.is_active is True

    def test_clear_active_nodes(self, viewmodel, simple_graph):
        """Test clearing all active nodes."""
        viewmodel.load_graph(simple_graph)

        viewmodel.set_node_active("A", True)
        viewmodel.set_node_active("B", True)

        viewmodel.clear_active_nodes()

        assert viewmodel.get_node("A").is_active is False
        assert viewmodel.get_node("B").is_active is False


class TestSelection:
    """Test selection state (read-only in Stage 1)."""

    def test_get_selected_nodes_empty(self, viewmodel):
        """Test getting selected nodes when none selected."""
        assert viewmodel.get_selected_nodes() == []

    def test_get_selected_edges_empty(self, viewmodel):
        """Test getting selected edges when none selected."""
        assert viewmodel.get_selected_edges() == []

    def test_is_node_selected_false(self, viewmodel, simple_graph):
        """Test checking if node is selected (should be False)."""
        viewmodel.load_graph(simple_graph)
        assert viewmodel.is_node_selected("A") is False

    def test_is_edge_selected_false(self, viewmodel, simple_graph):
        """Test checking if edge is selected (should be False)."""
        viewmodel.load_graph(simple_graph)
        edges = viewmodel.get_edges()
        assert viewmodel.is_edge_selected(edges[0].edge_id) is False


class TestStatistics:
    """Test statistics and utility methods."""

    def test_get_node_count(self, viewmodel, simple_graph):
        """Test getting node count."""
        assert viewmodel.get_node_count() == 0

        viewmodel.load_graph(simple_graph)
        assert viewmodel.get_node_count() == 3

    def test_get_edge_count(self, viewmodel, simple_graph):
        """Test getting edge count."""
        assert viewmodel.get_edge_count() == 0

        viewmodel.load_graph(simple_graph)
        assert viewmodel.get_edge_count() == 3

    def test_get_bounds(self, viewmodel, simple_graph):
        """Test getting bounding box of nodes."""
        viewmodel.load_graph(simple_graph)
        bounds = viewmodel.get_bounds()

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds

        assert min_x == 0
        assert min_y == 0
        assert max_x == 100
        assert max_y == 100

    def test_get_bounds_empty(self, viewmodel):
        """Test getting bounds with no nodes."""
        bounds = viewmodel.get_bounds()
        assert bounds is None


class TestObservableProperties:
    """Test that observable properties work correctly."""

    def test_viewport_changed_notifies(self, viewmodel):
        """Test viewport_changed property notifies observers."""
        observed_values = []

        def observer(old, new):
            observed_values.append((old, new))

        viewmodel.observe_property("viewport_changed", observer)

        viewmodel.zoom_in()

        assert len(observed_values) > 0
        assert observed_values[0][1] > observed_values[0][0]

    def test_nodes_changed_notifies(self, viewmodel, simple_graph):
        """Test nodes_changed property notifies observers."""
        observed_values = []

        def observer(old, new):
            observed_values.append((old, new))

        viewmodel.observe_property("nodes_changed", observer)

        viewmodel.load_graph(simple_graph)

        assert len(observed_values) > 0
        assert observed_values[0][1] > observed_values[0][0]


class TestSelectionInteractive:
    """Test Stage 2 interactive selection features."""

    def test_select_node(self, viewmodel, simple_graph):
        """Test selecting a single node."""
        viewmodel.load_graph(simple_graph)

        viewmodel.select_node("A")

        assert viewmodel.is_node_selected("A")
        assert "A" in viewmodel.get_selected_nodes()
        assert viewmodel.get_node("A").is_selected

    def test_select_node_add_to_selection(self, viewmodel, simple_graph):
        """Test adding nodes to selection."""
        viewmodel.load_graph(simple_graph)

        viewmodel.select_node("A")
        viewmodel.select_node("B", add_to_selection=True)

        assert viewmodel.is_node_selected("A")
        assert viewmodel.is_node_selected("B")
        assert len(viewmodel.get_selected_nodes()) == 2

    def test_select_node_clears_previous(self, viewmodel, simple_graph):
        """Test that selecting without add_to_selection clears previous."""
        viewmodel.load_graph(simple_graph)

        viewmodel.select_node("A")
        viewmodel.select_node("B")  # Should clear A

        assert not viewmodel.is_node_selected("A")
        assert viewmodel.is_node_selected("B")
        assert len(viewmodel.get_selected_nodes()) == 1

    def test_deselect_node(self, viewmodel, simple_graph):
        """Test deselecting a node."""
        viewmodel.load_graph(simple_graph)

        viewmodel.select_node("A")
        assert viewmodel.is_node_selected("A")

        viewmodel.deselect_node("A")
        assert not viewmodel.is_node_selected("A")
        assert len(viewmodel.get_selected_nodes()) == 0

    def test_select_nodes_in_rect(self, viewmodel, simple_graph):
        """Test selecting nodes in a rectangular region."""
        viewmodel.load_graph(simple_graph)

        # Select nodes in rect that includes A and B
        viewmodel.select_nodes_in_rect(-50, -50, 150, 50)

        assert viewmodel.is_node_selected("A")
        assert viewmodel.is_node_selected("B")
        assert not viewmodel.is_node_selected("C")  # C is at (50, 100), outside rect

    def test_select_nodes_in_rect_normalized(self, viewmodel, simple_graph):
        """Test that rect selection handles inverted coordinates."""
        viewmodel.load_graph(simple_graph)

        # Inverted rect (bottom-right to top-left)
        viewmodel.select_nodes_in_rect(150, 50, -50, -50)

        # Should work the same as normal order
        assert viewmodel.is_node_selected("A")
        assert viewmodel.is_node_selected("B")

    def test_clear_selection(self, viewmodel, simple_graph):
        """Test clearing all selection."""
        viewmodel.load_graph(simple_graph)

        viewmodel.select_node("A")
        viewmodel.select_node("B", add_to_selection=True)
        assert len(viewmodel.get_selected_nodes()) == 2

        viewmodel.clear_selection()

        assert len(viewmodel.get_selected_nodes()) == 0
        assert not viewmodel.get_node("A").is_selected
        assert not viewmodel.get_node("B").is_selected

    def test_select_edge(self, viewmodel, simple_graph):
        """Test selecting an edge."""
        viewmodel.load_graph(simple_graph)
        edges = viewmodel.get_edges()
        edge_id = edges[0].edge_id

        viewmodel.select_edge(edge_id)

        assert viewmodel.is_edge_selected(edge_id)
        assert edge_id in viewmodel.get_selected_edges()

    def test_deselect_edge(self, viewmodel, simple_graph):
        """Test deselecting an edge."""
        viewmodel.load_graph(simple_graph)
        edges = viewmodel.get_edges()
        edge_id = edges[0].edge_id

        viewmodel.select_edge(edge_id)
        assert viewmodel.is_edge_selected(edge_id)

        viewmodel.deselect_edge(edge_id)
        assert not viewmodel.is_edge_selected(edge_id)
