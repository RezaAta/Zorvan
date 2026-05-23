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

import pytest

from zorvan.Core.BackpropGraphForwardProcessing import BackpropGraphForwardProcessing
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from zorvan.Nodes.AdditionNode import AdditionNode
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.SigmoidNode import SigmoidNode


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


class TestSequenceFinderXORManualParity:
    """Ensure automatic sequence matches XOR manual example ordering."""

    def setup_method(self):
        self.graph = Graph()

        mlp_graph = MLPGraphForwardProcessing(
            numInputs=2,
            numOutputs=1,
            numHiddenLayers=1,
            hiddenLayerSizes=[2],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlp_graph.BuildMLP()

        X_train = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
        y_train = [[0.0], [1.0], [1.0], [0.0]]
        mlp_graph.LoadData(X_train, y_train)

        backprop_graph = BackpropGraphForwardProcessing(mlp_graph, learningRate=0.5)
        backprop_graph.BuildBackprop()

        for node in mlp_graph.nodes:
            self.graph.AddNode(node)
        for node in backprop_graph.nodes:
            self.graph.AddNode(node)

        self.graph.starting_nodes = list(mlp_graph.starting_nodes)
        self.graph.stopping_nodes = list(getattr(mlp_graph, "stopping_nodes", []))
        self.graph.UpdateAdjacencyMatrix()

        self.processor = GraphProcessor(self.graph)

    def test_sequence_matches_manual_xor_steps(self):
        expected_steps = [
            ["Add_L0N0", "Add_L0N1"],
            ["Act_L0N0", "Act_L0N1"],
            ["Mul_H0N0y0", "Mul_H0N1y0", "D_H0N0", "D_H0N1"],
            ["Add_y0"],
            ["y0"],
            ["Error_y0", "D_y0"],
            ["EG_y0"],
            ["LRMult_y0", "WG_H0N0W0", "WG_H0N1W0"],
            ["dW_H0N0y0", "dW_H0N1y0", "WGS_H0N0", "WGS_H0N1", "B_y0"],
            ["EG_H0N0", "EG_H0N1", "W_H0N0y0", "W_H0N1y0"],
            ["LRMult_H0N0", "LRMult_H0N1"],
            ["dW_x0H0N0", "dW_x0H0N1", "dW_x1H0N0", "dW_x1H0N1", "B_H0N0", "B_H0N1"],
            ["W_x0H0N0", "W_x0H0N1", "W_x1H0N0", "W_x1H0N1"],
            ["x0", "x1", "L_y0"],
        ]

        self.processor.mark_source_nodes_as_processed()
        self.processor.mark_container_nodes_as_processed()

        seq_result = self.processor.find_execution_sequence(
            starting_nodes=self.graph.starting_nodes,
            stopping_nodes=self.graph.stopping_nodes,
            include_remaining_source_nodes=True,
        )

        starting_set = set(self.graph.starting_nodes)
        filtered_sequence = []
        for step in seq_result["sequence"]:
            filtered_step = [n for n in step if n not in starting_set]
            if filtered_step:
                filtered_sequence.append(filtered_step)

        actual_step_names = [[node.name for node in step] for step in filtered_sequence]
        assert actual_step_names == expected_steps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
