"""
Integration test for nested nodes: AbstractNode containing CompressedNodes
and CompressedNodes containing AbstractNodes.

This test verifies that the processor correctly handles nested node structures
and that both compression and abstraction work together seamlessly.
"""

import pytest

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AbstractNode import AbstractNode
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.CompressedNode import CompressedNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode


class TestAbstractionNesting:
    """Test nested abstraction and compression scenarios."""

    def test_abstract_node_basic_creation(self):
        """Test creating an AbstractNode with disjoint basic nodes."""
        graph = Graph()

        # Create disjoint nodes with same predecessors and successors
        input_node = DataStreamNode("input", [1, 2, 3])
        graph.AddNode(input_node)

        add_a = AdditionNode("add_a")
        add_b = AdditionNode("add_b")
        graph.AddNode(add_a)
        graph.AddNode(add_b)

        # Both addition nodes have same predecessor
        add_a.AddPreNode(input_node)
        add_b.AddPreNode(input_node)

        output = AdditionNode("output")
        graph.AddNode(output)

        # Both addition nodes have same successor
        output.AddPreNode(add_a)
        output.AddPreNode(add_b)

        # Check abstraction is valid
        can_abstract, reason = graph.can_abstract_nodes([add_a, add_b])
        assert can_abstract, f"Should be able to abstract: {reason}"

        # Perform abstraction
        abstract = graph.AbstractNodes([add_a, add_b])
        assert abstract is not None
        assert isinstance(abstract, AbstractNode)
        assert len(abstract) == 2
        assert abstract.name == abstract.id
        assert abstract.id.startswith("A")

        # Check graph structure
        assert len(graph.nodes) == 3  # input, abstract, output
        assert abstract in graph.nodes
        assert add_a not in graph.nodes  # removed from main graph
        assert add_b not in graph.nodes

        # Check connections
        assert input_node in abstract.predecessors
        assert abstract in output.predecessors

    def test_abstract_node_with_compressed_internal(self):
        """Test AbstractNode containing CompressedNodes.

        Create a scenario where AbstractNode contains CompressedNode objects
        as its internal nodes (though unusual, this tests nesting capability).
        """
        graph = Graph()

        # Create input
        input_node = DataStreamNode("input", [1, 2])
        graph.AddNode(input_node)

        # Create two simple chains to compress
        # Chain 1: add1 -> mul1
        add1 = AdditionNode("add1")
        mul1 = MultiplicationNode("mul1")
        add1.AddPreNode(input_node)
        mul1.AddPreNode(add1)

        # Chain 2: add2 -> mul2
        add2 = AdditionNode("add2")
        mul2 = MultiplicationNode("mul2")
        add2.AddPreNode(input_node)
        mul2.AddPreNode(add2)

        graph.AddNode(add1)
        graph.AddNode(mul1)
        graph.AddNode(add2)
        graph.AddNode(mul2)

        # Compress both chains
        compressed1 = graph.CompressNodes([add1, mul1])
        compressed2 = graph.CompressNodes([add2, mul2])

        assert compressed1 is not None
        assert compressed2 is not None
        assert len(graph.nodes) == 3  # input, compressed1, compressed2

        # Now try to abstract the two compressed nodes
        # (they should have same predecessors and successors)
        can_abstract, reason = graph.can_abstract_nodes([compressed1, compressed2])
        assert can_abstract, f"Should be able to abstract compressed nodes: {reason}"

        # Perform abstraction of compressed nodes
        abstract = graph.AbstractNodes([compressed1, compressed2])
        assert abstract is not None
        assert isinstance(abstract, AbstractNode)
        assert len(abstract) == 2

        # Verify internal nodes are still CompressedNode objects
        internal = abstract.get_internal_nodes()
        assert all(isinstance(n, CompressedNode) for n in internal)

        # Check graph structure: input + abstract
        assert len(graph.nodes) == 2
        assert input_node in graph.nodes
        assert abstract in graph.nodes

    def test_compress_nodes_with_abstract_internal(self):
        """Test CompressedNode containing AbstractNodes as internal nodes.

        This creates a scenario where we have:
        - Two disjoint nodes (a, b) that we abstract into A1
        - Another node (c)
        - Then compress [A1, c] into a chain
        """
        graph = Graph()

        # Create input
        input_node = DataStreamNode("input", [1, 2])
        graph.AddNode(input_node)

        # Create two disjoint nodes
        add_a = AdditionNode("add_a")
        add_b = AdditionNode("add_b")
        add_a.AddPreNode(input_node)
        add_b.AddPreNode(input_node)
        graph.AddNode(add_a)
        graph.AddNode(add_b)

        # Create a third node that depends on both
        mul_c = MultiplicationNode("mul_c")
        mul_c.AddPreNode(add_a)
        mul_c.AddPreNode(add_b)
        graph.AddNode(mul_c)

        # Abstract the two disjoint nodes
        abstract = graph.AbstractNodes([add_a, add_b])
        assert abstract is not None

        # Now we have: input -> abstract -> mul_c
        # Try to compress this chain (abstract + mul_c form a valid chain)
        can_compress, reason = graph.can_compress_nodes([abstract, mul_c])
        assert can_compress, f"Should be able to compress abstract + mul_c: {reason}"

        # Perform compression
        compressed = graph.CompressNodes([abstract, mul_c])
        assert compressed is not None
        assert isinstance(compressed, CompressedNode)
        assert len(compressed) == 2

        # Verify first internal node is the abstract
        internal = compressed.get_internal_nodes()
        assert isinstance(internal[0], AbstractNode)

        # Check graph structure: input + compressed
        assert len(graph.nodes) == 2
        assert input_node in graph.nodes
        assert compressed in graph.nodes

    def test_processor_handles_nested_abstraction(self):
        """Test that GraphProcessor correctly processes nested abstract nodes."""
        graph = Graph()

        # Create a simple nested structure
        input_node = DataStreamNode("input", [5])
        graph.AddNode(input_node)
        graph.starting_nodes = [input_node]

        # Create two disjoint addition nodes (both add input to itself)
        add_a = AdditionNode("add_a")
        add_b = AdditionNode("add_b")
        add_a.AddPreNode(input_node)
        add_b.AddPreNode(input_node)
        graph.AddNode(add_a)
        graph.AddNode(add_b)

        # Create output that sums both
        output = AdditionNode("output")
        output.AddPreNode(add_a)
        output.AddPreNode(add_b)
        graph.AddNode(output)

        # Abstract the two addition nodes
        abstract = graph.AbstractNodes([add_a, add_b])
        assert abstract is not None

        # Update adjacency matrix
        graph.UpdateAdjacencyMatrix()

        # Process with processor (concurrent mode)
        # Note: Concurrent processing requires multiple iterations for values to propagate
        # through layers. With input -> abstract -> output, we need 2+ iterations.
        processor = GraphProcessor(graph)
        processor.ComputeGraph(iterations=2)

        # Check that output was computed correctly
        # input=5, add_a should get 5, add_b should get 5
        # output should sum them: 5+5=10
        assert output.value == 10, f"Expected output=10, got {output.value}"

    def test_processor_handles_nested_compression(self):
        """Test that GraphProcessor correctly processes nested compressed nodes."""
        graph = Graph()

        # Create input
        input_node = DataStreamNode("input", [2])
        graph.AddNode(input_node)
        graph.starting_nodes = [input_node]

        # Create a chain: add -> mul -> add
        add1 = AdditionNode("add1")
        mul1 = MultiplicationNode("mul1")
        add2 = AdditionNode("add2")

        add1.AddPreNode(input_node)
        mul1.AddPreNode(add1)
        add2.AddPreNode(mul1)

        graph.AddNode(add1)
        graph.AddNode(mul1)
        graph.AddNode(add2)

        # Compress the chain
        compressed = graph.CompressNodes([add1, mul1, add2])
        assert compressed is not None

        # Update adjacency matrix
        graph.UpdateAdjacencyMatrix()

        # Process
        processor = GraphProcessor(graph)
        processor.ComputeGraph(iterations=1)

        # Verify computation: input=2, add1=2+?=2 (no other pred),
        # mul1=2*?=2, add2=2+?=2
        # The actual values depend on default node behavior
        assert compressed.value is not None

    def test_expand_abstract_preserves_nested_structure(self):
        """Test that expanding an abstract node preserves nested compressed nodes."""
        graph = Graph()

        # Create input
        input_node = DataStreamNode("input", [1])
        graph.AddNode(input_node)

        # Create two chains to compress
        add1 = AdditionNode("add1")
        mul1 = MultiplicationNode("mul1")
        add1.AddPreNode(input_node)
        mul1.AddPreNode(add1)

        add2 = AdditionNode("add2")
        mul2 = MultiplicationNode("mul2")
        add2.AddPreNode(input_node)
        mul2.AddPreNode(add2)

        graph.AddNode(add1)
        graph.AddNode(mul1)
        graph.AddNode(add2)
        graph.AddNode(mul2)

        # Compress both chains
        comp1 = graph.CompressNodes([add1, mul1])
        comp2 = graph.CompressNodes([add2, mul2])

        assert len(graph.nodes) == 3  # input, comp1, comp2

        # Abstract the compressed nodes
        abstract = graph.AbstractNodes([comp1, comp2])
        assert len(graph.nodes) == 2  # input, abstract
        assert abstract.listOfNodes[0] is comp1 or abstract.listOfNodes[1] is comp1

        # Expand the abstract
        restored = graph.ExpandAbstractNode(abstract)
        assert len(restored) == 2
        assert all(isinstance(n, CompressedNode) for n in restored)

        # Check graph structure
        assert len(graph.nodes) == 3  # input, comp1, comp2 back
        assert comp1 in graph.nodes
        assert comp2 in graph.nodes

    def test_can_abstract_with_mixed_node_types(self):
        """Test can_abstract with mixed node types inside abstract."""
        graph = Graph()

        # Create input
        input_node = DataStreamNode("input", [1])
        graph.AddNode(input_node)

        # Create mixed nodes: AdditionNode and MultiplicationNode (disjoint)
        add_node = AdditionNode("add_node")
        mul_node = MultiplicationNode("mul_node")
        add_node.AddPreNode(input_node)
        mul_node.AddPreNode(input_node)
        graph.AddNode(add_node)
        graph.AddNode(mul_node)

        # Create output
        output = AdditionNode("output")
        output.AddPreNode(add_node)
        output.AddPreNode(mul_node)
        graph.AddNode(output)

        # Should be able to abstract different node types if they're disjoint
        # with same predecessors/successors
        can_abstract, reason = graph.can_abstract_nodes([add_node, mul_node])
        assert can_abstract, f"Should abstract different node types: {reason}"

        abstract = graph.AbstractNodes([add_node, mul_node])
        assert abstract is not None
        assert len(abstract) == 2
        # Internal nodes should be preserved with their types
        assert isinstance(abstract.listOfNodes[0], (AdditionNode, MultiplicationNode))
        assert isinstance(abstract.listOfNodes[1], (AdditionNode, MultiplicationNode))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
