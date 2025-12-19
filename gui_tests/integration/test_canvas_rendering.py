"""
Integration tests for CanvasView (headless mode).

Tests the rendering logic of CanvasView without requiring a display.
Uses QT_QPA_PLATFORM=offscreen for headless testing.
"""

import os
import pytest

# Set up headless mode before importing PyQt
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtTest import QTest
    from PyQt6.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel
    from gui_framework.views.canvas_view import CanvasView


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


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


@pytest.fixture
def simple_graph():
    """Create a simple graph with 3 nodes."""
    graph = MockGraph()
    
    node_a = MockNode("A", 0, 0)
    node_b = MockNode("B", 100, 0)
    node_c = MockNode("C", 50, 100)
    
    node_b.predecessors = [node_a]
    node_c.predecessors = [node_a, node_b]
    
    graph.nodes = [node_a, node_b, node_c]
    return graph


class TestCanvasViewInit:
    """Test CanvasView initialization."""
    
    def test_canvas_view_creation(self, qapp, simple_graph):
        """Test creating a canvas view."""
        vm = CanvasViewModel(simple_graph)
        view = CanvasView(vm)
        
        assert view is not None
        assert view.get_scene() is not None
        assert view.get_view() is not None
    
    def test_canvas_view_has_viewmodel(self, qapp, simple_graph):
        """Test canvas view has access to viewmodel."""
        vm = CanvasViewModel(simple_graph)
        view = CanvasView(vm)
        
        assert view.get_viewmodel() == vm


class TestNodeRendering:
    """Test node rendering in canvas view."""
    
    def test_nodes_rendered_on_load(self, qapp, simple_graph):
        """Test that nodes are rendered when graph is loaded."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        # Should have 3 node items
        assert len(view._node_items) == 3
        assert "A" in view._node_items
        assert "B" in view._node_items
        assert "C" in view._node_items
    
    def test_node_positions(self, qapp, simple_graph):
        """Test that node positions are rendered correctly."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        node_a_item = view._node_items["A"]
        node_b_item = view._node_items["B"]
        node_c_item = view._node_items["C"]
        
        assert node_a_item.scenePos().x() == 0
        assert node_a_item.scenePos().y() == 0
        assert node_b_item.scenePos().x() == 100
        assert node_b_item.scenePos().y() == 0
        assert node_c_item.scenePos().x() == 50
        assert node_c_item.scenePos().y() == 100
    
    def test_node_updates_on_position_change(self, qapp, simple_graph):
        """Test that nodes update when positions change."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        # Change node A position
        vm.update_node_position("A", 200, 300)
        
        # Node item should update
        node_a_item = view._node_items["A"]
        assert node_a_item.scenePos().x() == 200
        assert node_a_item.scenePos().y() == 300


class TestEdgeRendering:
    """Test edge rendering in canvas view."""
    
    def test_edges_rendered_on_load(self, qapp, simple_graph):
        """Test that edges are rendered when graph is loaded."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        # Should have 3 edges (A->B, A->C, B->C)
        assert len(view._edge_items) == 3
    
    def test_edge_connects_nodes(self, qapp, simple_graph):
        """Test that edges connect the correct nodes."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        # Find edge A->B
        edge_ab = None
        for edge in view._edge_items.values():
            if edge.source_item.node_id == "A" and edge.target_item.node_id == "B":
                edge_ab = edge
                break
        
        assert edge_ab is not None
        assert edge_ab.source_item == view._node_items["A"]
        assert edge_ab.target_item == view._node_items["B"]


class TestViewportControl:
    """Test viewport zoom/pan controls."""
    
    def test_zoom_in(self, qapp, simple_graph):
        """Test zooming in updates the view."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        initial_zoom = vm.get_viewport().zoom_level
        vm.zoom_in(1.5)
        
        # Viewport should have updated
        assert vm.get_viewport().zoom_level == initial_zoom * 1.5
    
    def test_zoom_out(self, qapp, simple_graph):
        """Test zooming out updates the view."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        initial_zoom = vm.get_viewport().zoom_level
        vm.zoom_out(2.0)
        
        # Viewport should have updated
        assert vm.get_viewport().zoom_level == initial_zoom / 2.0
    
    def test_reset_viewport(self, qapp, simple_graph):
        """Test resetting viewport."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        # Zoom and pan
        vm.zoom_in(2.0)
        vm.pan(100, 200)
        
        # Reset
        vm.reset_viewport()
        vp = vm.get_viewport()
        
        assert vp.zoom_level == 1.0
        assert vp.center_x == 0
        assert vp.center_y == 0


class TestNodeVisualization:
    """Test node color and active state visualization."""
    
    def test_node_color_update(self, qapp, simple_graph):
        """Test that node color updates are reflected in view."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        # Set node color
        vm.set_node_color("A", "#FF0000")
        
        # Node item should update (check that it doesn't crash)
        node_a_item = view._node_items["A"]
        assert node_a_item is not None
    
    def test_node_active_state(self, qapp, simple_graph):
        """Test that node active state is visualized."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        # Set node active
        vm.set_node_active("A", True)
        
        # Node item should update (check that it doesn't crash)
        node_a_item = view._node_items["A"]
        assert node_a_item is not None
    
    def test_clear_node_colors(self, qapp, simple_graph):
        """Test clearing node colors."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        # Set colors
        vm.set_node_color("A", "#FF0000")
        vm.set_node_color("B", "#00FF00")
        
        # Clear colors
        vm.clear_node_colors()
        
        # Nodes should still exist
        assert "A" in view._node_items
        assert "B" in view._node_items


class TestSceneManagement:
    """Test scene and item management."""
    
    def test_scene_contains_items(self, qapp, simple_graph):
        """Test that scene contains node and edge items."""
        vm = CanvasViewModel(simple_graph)
        vm.initialize()
        view = CanvasView(vm)
        
        scene = view.get_scene()
        items = scene.items()
        
        # Should have nodes, edges, and labels
        assert len(items) > 0
    
    def test_reload_graph(self, qapp):
        """Test reloading a different graph."""
        # First graph
        graph1 = MockGraph()
        graph1.nodes = [MockNode("A", 0, 0), MockNode("B", 100, 0)]
        
        vm = CanvasViewModel(graph1)
        vm.initialize()
        view = CanvasView(vm)
        
        assert len(view._node_items) == 2
        
        # Load second graph
        graph2 = MockGraph()
        graph2.nodes = [MockNode("X", 0, 0), MockNode("Y", 100, 0), MockNode("Z", 200, 0)]
        
        vm.load_graph(graph2)
        
        # Should have new nodes
        assert len(view._node_items) == 3
        assert "X" in view._node_items
        assert "Y" in view._node_items
        assert "Z" in view._node_items
        
        # Old nodes should be gone
        assert "A" not in view._node_items
        assert "B" not in view._node_items
