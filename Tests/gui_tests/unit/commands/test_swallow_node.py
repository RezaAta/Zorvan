"""
Test for the Swallow Node feature.

Tests the SwallowNodeCommand which removes nodes while reconnecting
their predecessors to their successors.
"""

from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import QPointF

# Skip if PyQt6 is not available
pytest.importorskip("PyQt6")


class TestSwallowNodeCommand:
    """Tests for SwallowNodeCommand."""

    def test_swallow_single_node_in_chain(self):
        """Test swallowing a node in a simple chain: a -> b -> c becomes a -> c."""
        from gui_framework.legacy import SwallowNodeCommand
        from zorvan.Core.Graph import Graph
        from zorvan.Nodes.DisplayNode import DisplayNode

        # Create a simple graph: a -> b -> c
        graph = Graph()
        node_a = DisplayNode("a")
        node_b = DisplayNode("b")
        node_c = DisplayNode("c")
        graph.AddNode(node_a)
        graph.AddNode(node_b)
        graph.AddNode(node_c)
        graph.ConnectPreNode(node_b, node_a)  # a -> b
        graph.ConnectPreNode(node_c, node_b)  # b -> c

        # Verify initial connections
        assert node_a in node_b.predecessors
        assert node_b in node_c.predecessors
        assert node_a not in node_c.predecessors

        # Create mock canvas and node_item
        canvas = MagicMock()
        canvas.node_items = {
            node_a: MagicMock(),
            node_b: MagicMock(),
            node_c: MagicMock(),
        }
        canvas.edge_items = []

        # Mock node_item for node_b
        node_item_b = MagicMock()
        node_item_b.node = node_b
        node_item_b.pos.return_value = QPointF(100, 100)
        node_item_b.manual_color = None

        # Create the command
        cmd = SwallowNodeCommand(canvas, graph, [node_item_b])

        # Verify command collected correct data
        assert len(cmd.swallowed_nodes) == 1
        assert cmd.swallowed_nodes[0][0] == node_b
        assert (node_a, node_b) in cmd.removed_edges  # Edge from a to b
        assert (node_b, node_c) in cmd.removed_edges  # Edge from b to c
        assert (node_a, node_c) in cmd.created_edges  # New bypass edge

    def test_swallow_preserves_multiple_predecessors(self):
        """Test swallowing a node with multiple predecessors."""
        from gui_framework.legacy import SwallowNodeCommand
        from zorvan.Core.Graph import Graph
        from zorvan.Nodes.DisplayNode import DisplayNode

        # Create graph: a1 -> b <- a2, b -> c
        graph = Graph()
        node_a1 = DisplayNode("a1")
        node_a2 = DisplayNode("a2")
        node_b = DisplayNode("b")
        node_c = DisplayNode("c")
        graph.AddNode(node_a1)
        graph.AddNode(node_a2)
        graph.AddNode(node_b)
        graph.AddNode(node_c)
        graph.ConnectPreNode(node_b, node_a1)  # a1 -> b
        graph.ConnectPreNode(node_b, node_a2)  # a2 -> b
        graph.ConnectPreNode(node_c, node_b)  # b -> c

        # Create mock canvas
        canvas = MagicMock()
        canvas.node_items = {
            node_a1: MagicMock(),
            node_a2: MagicMock(),
            node_b: MagicMock(),
            node_c: MagicMock(),
        }
        canvas.edge_items = []

        # Mock node_item for node_b
        node_item_b = MagicMock()
        node_item_b.node = node_b
        node_item_b.pos.return_value = QPointF(100, 100)
        node_item_b.manual_color = None

        # Create the command
        cmd = SwallowNodeCommand(canvas, graph, [node_item_b])

        # Both a1 and a2 should connect to c
        assert (node_a1, node_c) in cmd.created_edges
        assert (node_a2, node_c) in cmd.created_edges

    def test_swallow_preserves_multiple_successors(self):
        """Test swallowing a node with multiple successors."""
        from gui_framework.legacy import SwallowNodeCommand
        from zorvan.Core.Graph import Graph
        from zorvan.Nodes.DisplayNode import DisplayNode

        # Create graph: a -> b -> c1, b -> c2
        graph = Graph()
        node_a = DisplayNode("a")
        node_b = DisplayNode("b")
        node_c1 = DisplayNode("c1")
        node_c2 = DisplayNode("c2")
        graph.AddNode(node_a)
        graph.AddNode(node_b)
        graph.AddNode(node_c1)
        graph.AddNode(node_c2)
        graph.ConnectPreNode(node_b, node_a)  # a -> b
        graph.ConnectPreNode(node_c1, node_b)  # b -> c1
        graph.ConnectPreNode(node_c2, node_b)  # b -> c2

        # Create mock canvas
        canvas = MagicMock()
        canvas.node_items = {
            node_a: MagicMock(),
            node_b: MagicMock(),
            node_c1: MagicMock(),
            node_c2: MagicMock(),
        }
        canvas.edge_items = []

        # Mock node_item for node_b
        node_item_b = MagicMock()
        node_item_b.node = node_b
        node_item_b.pos.return_value = QPointF(100, 100)
        node_item_b.manual_color = None

        # Create the command
        cmd = SwallowNodeCommand(canvas, graph, [node_item_b])

        # a should connect to both c1 and c2
        assert (node_a, node_c1) in cmd.created_edges
        assert (node_a, node_c2) in cmd.created_edges

    def test_swallow_multiple_nodes(self):
        """Test swallowing multiple nodes at once: a -> b -> c -> d, swallow b,c => a -> d."""
        from gui_framework.legacy import SwallowNodeCommand
        from zorvan.Core.Graph import Graph
        from zorvan.Nodes.DisplayNode import DisplayNode

        # Create a chain: a -> b -> c -> d
        graph = Graph()
        node_a = DisplayNode("a")
        node_b = DisplayNode("b")
        node_c = DisplayNode("c")
        node_d = DisplayNode("d")
        graph.AddNode(node_a)
        graph.AddNode(node_b)
        graph.AddNode(node_c)
        graph.AddNode(node_d)
        graph.ConnectPreNode(node_b, node_a)  # a -> b
        graph.ConnectPreNode(node_c, node_b)  # b -> c
        graph.ConnectPreNode(node_d, node_c)  # c -> d

        # Create mock canvas
        canvas = MagicMock()
        canvas.node_items = {
            node_a: MagicMock(),
            node_b: MagicMock(),
            node_c: MagicMock(),
            node_d: MagicMock(),
        }
        canvas.edge_items = []

        # Mock node_items for b and c (swallowing both)
        node_item_b = MagicMock()
        node_item_b.node = node_b
        node_item_b.pos.return_value = QPointF(100, 100)
        node_item_b.manual_color = None

        node_item_c = MagicMock()
        node_item_c.node = node_c
        node_item_c.pos.return_value = QPointF(200, 100)
        node_item_c.manual_color = None

        # Create the command to swallow both b and c
        cmd = SwallowNodeCommand(canvas, graph, [node_item_b, node_item_c])

        # After swallowing b and c, a should connect directly to d
        # Since b's successor (c) is also being swallowed, no edge from a to c
        # Since c's predecessor (b) is also being swallowed, no edge from b to d
        # Only edge should be a -> d
        assert (node_a, node_d) in cmd.created_edges
        # Edges to swallowed nodes should not be created
        assert (node_a, node_c) not in cmd.created_edges
        assert (node_b, node_d) not in cmd.created_edges

    def test_swallow_avoids_duplicate_edges(self):
        """Test that swallowing doesn't create duplicate edges."""
        from gui_framework.legacy import SwallowNodeCommand
        from zorvan.Core.Graph import Graph
        from zorvan.Nodes.DisplayNode import DisplayNode

        # Create graph where a already connects to c: a -> b -> c, a -> c
        graph = Graph()
        node_a = DisplayNode("a")
        node_b = DisplayNode("b")
        node_c = DisplayNode("c")
        graph.AddNode(node_a)
        graph.AddNode(node_b)
        graph.AddNode(node_c)
        graph.ConnectPreNode(node_b, node_a)  # a -> b
        graph.ConnectPreNode(node_c, node_b)  # b -> c
        graph.ConnectPreNode(node_c, node_a)  # a -> c (already exists)

        # Create mock canvas
        canvas = MagicMock()
        canvas.node_items = {
            node_a: MagicMock(),
            node_b: MagicMock(),
            node_c: MagicMock(),
        }
        canvas.edge_items = []

        # Mock node_item for node_b
        node_item_b = MagicMock()
        node_item_b.node = node_b
        node_item_b.pos.return_value = QPointF(100, 100)
        node_item_b.manual_color = None

        # Create the command
        cmd = SwallowNodeCommand(canvas, graph, [node_item_b])

        # a -> c should NOT be in created_edges since it already exists
        assert (node_a, node_c) not in cmd.created_edges


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
