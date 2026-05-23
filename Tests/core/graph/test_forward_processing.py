"""
Tests for GraphProcessor forward processing execution.
"""

from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.AdditionNode import AdditionNode


class TestForwardProcessingExecution:
    """Test that GraphProcessor.ForwardProcessing executes the static sequence."""

    def setup_method(self):
        self.graph = Graph()
        self.a = AdditionNode("a")
        self.b = AdditionNode("b")

        self.b.AddPreNode(self.a)

        self.graph.AddNode(self.a, self.b)
        self.graph.starting_nodes = [self.a]
        self.graph.UpdateAdjacencyMatrix()

        self.a.value = 5
        self.processor = GraphProcessor(self.graph)

    def test_forward_processing_returns_stats(self):
        result = self.processor.ForwardProcessing(iterations=1)
        assert "iterations_completed" in result
        assert "steps_per_iteration" in result
        assert "sequence_info" in result

    def test_forward_processing_completes_iterations(self):
        result = self.processor.ForwardProcessing(iterations=3)
        assert result["iterations_completed"] == 3

    def test_forward_processing_step_count(self):
        result = self.processor.ForwardProcessing(iterations=1)
        assert result["steps_per_iteration"] == 2
