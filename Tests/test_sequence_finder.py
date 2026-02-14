"""
Tests for the sequence finder algorithm in GraphProcessor.

Tests cover:
1. Linear chain: a -> b -> c -> d
2. Diamond DAG: a -> b,c -> d
3. Multiple starting nodes
4. Remaining source nodes (not in starting_nodes)
5. Disconnected components
6. Stopping nodes behavior
"""

import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode


class TestSequenceFinderLinearChain:
    """Test sequence finder with a simple linear chain: a -> b -> c -> d"""

    def setup_method(self):
        """Create a linear chain graph."""
        self.graph = Graph()
        self.a = AdditionNode("a")
        self.b = AdditionNode("b")
        self.c = AdditionNode("c")
        self.d = AdditionNode("d")

        # Build chain: a -> b -> c -> d
        self.b.AddPreNode(self.a)
        self.c.AddPreNode(self.b)
        self.d.AddPreNode(self.c)

        self.graph.AddNode(self.a, self.b, self.c, self.d)
        self.graph.starting_nodes = [self.a]
        self.graph.UpdateAdjacencyMatrix()

        self.processor = GraphProcessor(self.graph)

    def test_sequence_has_four_steps(self):
        """Each node should be in its own step."""
        result = self.processor.find_execution_sequence()
        assert len(result["sequence"]) == 4

    def test_sequence_order_is_correct(self):
        """Nodes should appear in order: a, b, c, d."""
        result = self.processor.find_execution_sequence()
        seq = result["sequence"]
        assert seq[0] == [self.a]
        assert seq[1] == [self.b]
        assert seq[2] == [self.c]
        assert seq[3] == [self.d]

    def test_all_nodes_processed(self):
        """All nodes should be in processed_nodes."""
        result = self.processor.find_execution_sequence()
        assert result["complete"] is True
        assert len(result["remaining_nodes"]) == 0
        assert len(result["processed_nodes"]) == 4


class TestSequenceFinderDiamondDAG:
    """Test sequence finder with a diamond DAG: a -> b,c -> d"""

    def setup_method(self):
        """Create a diamond DAG graph."""
        self.graph = Graph()
        self.a = AdditionNode("a")
        self.b = AdditionNode("b")
        self.c = AdditionNode("c")
        self.d = AdditionNode("d")

        # Build diamond: a -> b, a -> c, b -> d, c -> d
        self.b.AddPreNode(self.a)
        self.c.AddPreNode(self.a)
        self.d.AddPreNode(self.b, self.c)

        self.graph.AddNode(self.a, self.b, self.c, self.d)
        self.graph.starting_nodes = [self.a]
        self.graph.UpdateAdjacencyMatrix()

        self.processor = GraphProcessor(self.graph)

    def test_sequence_has_three_steps(self):
        """Step 0: a, Step 1: b and c (parallel), Step 2: d."""
        result = self.processor.find_execution_sequence()
        assert len(result["sequence"]) == 3

    def test_parallel_nodes_in_same_step(self):
        """b and c should be in the same step."""
        result = self.processor.find_execution_sequence()
        seq = result["sequence"]
        step_1 = set(seq[1])
        assert self.b in step_1
        assert self.c in step_1

    def test_d_waits_for_both_predecessors(self):
        """d should only appear after both b and c are processed."""
        result = self.processor.find_execution_sequence()
        seq = result["sequence"]
        assert seq[2] == [self.d]


class TestSequenceFinderMultipleStartingNodes:
    """Test sequence finder with multiple starting nodes."""

    def setup_method(self):
        """Create a graph with two starting nodes: a,b -> c -> d"""
        self.graph = Graph()
        self.a = AdditionNode("a")
        self.b = AdditionNode("b")
        self.c = AdditionNode("c")
        self.d = AdditionNode("d")

        # Build: a -> c, b -> c, c -> d
        self.c.AddPreNode(self.a, self.b)
        self.d.AddPreNode(self.c)

        self.graph.AddNode(self.a, self.b, self.c, self.d)
        self.graph.starting_nodes = [self.a, self.b]
        self.graph.UpdateAdjacencyMatrix()

        self.processor = GraphProcessor(self.graph)

    def test_starting_nodes_in_first_step(self):
        """Both a and b should be in step 0."""
        result = self.processor.find_execution_sequence()
        step_0 = set(result["sequence"][0])
        assert self.a in step_0
        assert self.b in step_0

    def test_sequence_has_three_steps(self):
        """Step 0: a,b, Step 1: c, Step 2: d."""
        result = self.processor.find_execution_sequence()
        assert len(result["sequence"]) == 3


class TestSequenceFinderRemainingSourceNodes:
    """Test sequence finder when source nodes are not in starting_nodes."""

    def setup_method(self):
        """Create a graph where 'x' is a source not in starting_nodes."""
        self.graph = Graph()
        self.a = AdditionNode("a")
        self.b = AdditionNode("b")
        self.x = AdditionNode("x")  # Source node, not in starting_nodes
        self.y = AdditionNode("y")

        # Build: a -> b, x -> y (two separate chains)
        self.b.AddPreNode(self.a)
        self.y.AddPreNode(self.x)

        self.graph.AddNode(self.a, self.b, self.x, self.y)
        self.graph.starting_nodes = [self.a]  # Only a, not x
        self.graph.UpdateAdjacencyMatrix()

        self.processor = GraphProcessor(self.graph)

    def test_only_connected_nodes_sequenced(self):
        """Only a and b should be in sequence."""
        result = self.processor.find_execution_sequence()
        processed = result["processed_nodes"]
        assert self.a in processed
        assert self.b in processed
        assert self.x not in processed
        assert self.y not in processed

    def test_remaining_source_nodes_identified(self):
        """x should be identified as remaining source node."""
        result = self.processor.find_execution_sequence()
        assert self.x in result["remaining_source_nodes"]

    def test_remaining_non_source_nodes_identified(self):
        """y should be identified as remaining non-source node."""
        result = self.processor.find_execution_sequence()
        assert self.y in result["remaining_non_source_nodes"]

    def test_complete_is_false(self):
        """complete should be False since not all nodes are sequenced."""
        result = self.processor.find_execution_sequence()
        assert result["complete"] is False


class TestSequenceFinderStoppingNodes:
    """Test that stopping nodes don't trigger successor activation."""

    def setup_method(self):
        """Create a graph where 'w' is a stopping node."""
        self.graph = Graph()
        self.a = AdditionNode("a")
        self.w = AdditionNode("w")  # Will be a stopping node
        self.b = AdditionNode("b")

        # Build: a -> w -> b, but w is a stopping node
        self.w.AddPreNode(self.a)
        self.b.AddPreNode(self.w)

        self.graph.AddNode(self.a, self.w, self.b)
        self.graph.starting_nodes = [self.a]
        self.graph.stopping_nodes = [self.w]
        self.graph.UpdateAdjacencyMatrix()

        self.processor = GraphProcessor(self.graph)

    def test_stopping_node_is_sequenced(self):
        """w should still be added to the sequence."""
        result = self.processor.find_execution_sequence()
        assert self.w in result["processed_nodes"]

    def test_successor_of_stopping_node_not_sequenced(self):
        """b should not be sequenced since w is a stopping node."""
        result = self.processor.find_execution_sequence()
        assert self.b not in result["processed_nodes"]
        assert self.b in result["remaining_non_source_nodes"]


class TestForwardProcessingExecution:
    """Test that ForwardProcessing correctly executes the sequence."""

    def setup_method(self):
        """Create a simple chain for execution testing."""
        self.graph = Graph()
        self.a = AdditionNode("a")
        self.b = AdditionNode("b")

        self.b.AddPreNode(self.a)

        self.graph.AddNode(self.a, self.b)
        self.graph.starting_nodes = [self.a]
        self.graph.UpdateAdjacencyMatrix()

        # Set initial values
        self.a.value = 5

        self.processor = GraphProcessor(self.graph)

    def test_forward_processing_returns_stats(self):
        """ForwardProcessing should return execution statistics."""
        result = self.processor.ForwardProcessing(iterations=1)
        assert "iterations_completed" in result
        assert "steps_per_iteration" in result
        assert "sequence_info" in result

    def test_forward_processing_completes_iterations(self):
        """ForwardProcessing should complete the requested iterations."""
        result = self.processor.ForwardProcessing(iterations=3)
        assert result["iterations_completed"] == 3

    def test_forward_processing_step_count(self):
        """ForwardProcessing should report correct step count."""
        result = self.processor.ForwardProcessing(iterations=1)
        assert result["steps_per_iteration"] == 2  # a, then b


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
