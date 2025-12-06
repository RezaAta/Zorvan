"""
Tests for node compression feature.
"""

import pytest

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.CompressedNode import CompressedNode
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode


class TestCanCompressNodes:
    """Tests for Graph.can_compress_nodes() validation."""

    def test_needs_at_least_two_nodes(self):
        """Cannot compress a single node."""
        g = Graph()
        a = AdditionNode("a")
        g.AddNode(a)
        g.analyze_topology()

        can_compress, reason = g.can_compress_nodes([a])
        assert not can_compress
        assert "at least 2 nodes" in reason.lower()

    def test_valid_link_chain(self):
        """Can compress a chain of link nodes."""
        g = Graph()
        a = ContainerNode("a", value=1)
        b = SigmoidNode("b")
        c = SigmoidNode("c")
        d = SigmoidNode("d")

        g.AddNode(a, b, c, d)
        g.ConnectPreNode(b, a)
        g.ConnectPreNode(c, b)
        g.ConnectPreNode(d, c)
        g.analyze_topology()

        # b and c are link nodes
        can_compress, reason = g.can_compress_nodes([b, c])
        assert can_compress, reason

    def test_invalid_middle_node_with_external_predecessor(self):
        """Cannot compress if middle node has external predecessor."""
        g = Graph()
        a = ContainerNode("a", value=1)
        b = SigmoidNode("b")
        c = AdditionNode("c")  # Has 2 predecessors
        d = SigmoidNode("d")
        x = ContainerNode("x", value=2)  # External predecessor to c

        g.AddNode(a, b, c, d, x)
        g.ConnectPreNode(b, a)
        g.ConnectPreNode(c, b)
        g.ConnectPreNode(c, x)  # External connection
        g.ConnectPreNode(d, c)
        g.analyze_topology()

        can_compress, reason = g.can_compress_nodes([b, c])
        assert not can_compress
        # c is not a link node (has 2 predecessors)

    def test_disconnected_nodes_cannot_compress(self):
        """Cannot compress nodes that don't form a chain."""
        g = Graph()
        a = SigmoidNode("a")
        b = SigmoidNode("b")

        g.AddNode(a, b)
        # No connections between a and b
        g.analyze_topology()

        can_compress, reason = g.can_compress_nodes([a, b])
        assert not can_compress
        assert "chain" in reason.lower()


class TestCompressNodes:
    """Tests for Graph.CompressNodes() operation."""

    def test_compress_creates_compressed_node(self):
        """CompressNodes creates a CompressedNode with the chain."""
        g = Graph()
        a = ContainerNode("a", value=1)
        b = SigmoidNode("b")
        c = SigmoidNode("c")
        d = SigmoidNode("d")

        g.AddNode(a, b, c, d)
        g.ConnectPreNode(b, a)
        g.ConnectPreNode(c, b)
        g.ConnectPreNode(d, c)
        g.analyze_topology()

        compressed = g.CompressNodes([b, c])

        assert isinstance(compressed, CompressedNode)
        assert len(compressed.listOfNodes) == 2
        assert b in compressed.listOfNodes
        assert c in compressed.listOfNodes

    def test_compress_removes_original_nodes_from_graph(self):
        """Original nodes are removed from graph.nodes."""
        g = Graph()
        a = ContainerNode("a", value=1)
        b = SigmoidNode("b")
        c = SigmoidNode("c")
        d = SigmoidNode("d")

        g.AddNode(a, b, c, d)
        g.ConnectPreNode(b, a)
        g.ConnectPreNode(c, b)
        g.ConnectPreNode(d, c)
        g.analyze_topology()

        compressed = g.CompressNodes([b, c])

        assert b not in g.nodes
        assert c not in g.nodes
        assert compressed in g.nodes
        assert len(g.nodes) == 3  # a, compressed, d

    def test_compress_preserves_external_connections(self):
        """External connections are transferred to compressed node."""
        g = Graph()
        a = ContainerNode("a", value=1)
        b = SigmoidNode("b")
        c = SigmoidNode("c")
        d = SigmoidNode("d")

        g.AddNode(a, b, c, d)
        g.ConnectPreNode(b, a)
        g.ConnectPreNode(c, b)
        g.ConnectPreNode(d, c)
        g.analyze_topology()

        compressed = g.CompressNodes([b, c])

        # a -> compressed
        assert a in compressed.predecessors
        # compressed -> d
        assert compressed in d.predecessors


class TestCompressedNodeProcessing:
    """Tests for CompressedNode computation."""

    def test_compressed_node_processes_chain_sequentially(self):
        """CompressedNode processes internal nodes in order."""
        a = ContainerNode("a", value=0.5)
        sig1 = SigmoidNode("sig1")
        sig2 = SigmoidNode("sig2")

        sig1.predecessors = [a]
        sig2.predecessors = [sig1]

        compressed = CompressedNode("C1", [sig1, sig2])
        compressed.predecessors = [a]

        # Process
        compressed.Operation()

        # Values should be computed
        assert sig1.value != 0
        assert sig2.value != 0
        assert compressed.value == sig2.value

    def test_compressed_node_in_graph_processing(self):
        """CompressedNode works correctly with GraphProcessor."""
        g = Graph()
        a = ContainerNode("a", value=0.5)
        sig1 = SigmoidNode("sig1")
        sig2 = SigmoidNode("sig2")
        sig3 = SigmoidNode("sig3")

        g.AddNode(a, sig1, sig2, sig3)
        g.ConnectPreNode(sig1, a)
        g.ConnectPreNode(sig2, sig1)
        g.ConnectPreNode(sig3, sig2)
        g.starting_nodes = [a]
        g.analyze_topology()

        # Get expected values before compression
        processor1 = GraphProcessor(g)
        processor1.ComputeGraph(iterations=3)
        expected_sig3 = sig3.value

        # Reset and compress
        sig1.value = 0
        sig2.value = 0
        sig3.value = 0

        compressed = g.CompressNodes([sig1, sig2])

        # Process compressed graph
        processor2 = GraphProcessor(g)
        processor2.ComputeGraph(iterations=3)

        # Should get same final result
        assert abs(sig3.value - expected_sig3) < 0.0001


class TestDecompressNode:
    """Tests for Graph.DecompressNode() operation."""

    def test_decompress_restores_nodes(self):
        """DecompressNode restores internal nodes to graph."""
        g = Graph()
        a = ContainerNode("a", value=1)
        b = SigmoidNode("b")
        c = SigmoidNode("c")
        d = SigmoidNode("d")

        g.AddNode(a, b, c, d)
        g.ConnectPreNode(b, a)
        g.ConnectPreNode(c, b)
        g.ConnectPreNode(d, c)
        g.analyze_topology()

        compressed = g.CompressNodes([b, c])
        restored = g.DecompressNode(compressed, mode="full")

        assert b in restored
        assert c in restored
        assert b in g.nodes
        assert c in g.nodes
        assert compressed not in g.nodes

    def test_decompress_restores_connections(self):
        """DecompressNode restores proper connections."""
        g = Graph()
        a = ContainerNode("a", value=1)
        b = SigmoidNode("b")
        c = SigmoidNode("c")
        d = SigmoidNode("d")

        g.AddNode(a, b, c, d)
        g.ConnectPreNode(b, a)
        g.ConnectPreNode(c, b)
        g.ConnectPreNode(d, c)
        g.analyze_topology()

        g.CompressNodes([b, c])
        g.DecompressNode(g.nodes[-1], mode="full")  # Decompress last added

        # Check connections restored
        assert a in b.predecessors
        assert b in c.predecessors
        assert c in d.predecessors
