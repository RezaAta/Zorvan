"""
Tests for Multi-Graph Support feature (Phase 1).

This test module verifies:
1. Graph identity attributes (graph_id, graph_name, graph_color)
2. Sub-graph creation from nodes
3. Sub-graph metadata serialization
4. Sub-graph restoration from metadata
5. Duplicate sub-graph prevention
"""

import json
import os
import tempfile

import pytest

import ComputationalGraphs.Core.CGJsonIO as CGJsonIO
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode


class TestGraphIdentity:
    """Test graph identity attributes."""

    def test_graph_has_unique_id(self):
        """Each graph should have a unique ID."""
        g1 = Graph()
        g2 = Graph()
        assert g1.graph_id is not None
        assert g2.graph_id is not None
        assert g1.graph_id != g2.graph_id

    def test_graph_default_name(self):
        """Graph should have a default name."""
        g = Graph()
        assert g.graph_name == "Default Graph"

    def test_graph_custom_name(self):
        """Graph can be created with custom name."""
        g = Graph(name="My Custom Graph")
        assert g.graph_name == "My Custom Graph"

    def test_graph_has_color(self):
        """Each graph should have a color."""
        g = Graph()
        assert g.graph_color is not None
        assert g.graph_color.startswith("#")

    def test_mother_graph_flag(self):
        """Mother graph flag should be settable."""
        g = Graph()
        assert g.is_mother_graph is False
        g.set_as_mother_graph()
        assert g.is_mother_graph is True


class TestSubGraphCreation:
    """Test sub-graph creation from nodes."""

    def setup_method(self):
        """Create a graph with some nodes."""
        self.graph = Graph()
        self.graph.set_as_mother_graph()

        # Create nodes
        self.a = ContainerNode("a", value=1)
        self.b = ContainerNode("b", value=2)
        self.c = AdditionNode("c")
        self.d = MultiplicationNode("d")

        self.graph.AddNode(self.a, self.b, self.c, self.d)

        # Connect: a,b -> c -> d
        self.c.AddPreNode(self.a)
        self.c.AddPreNode(self.b)
        self.d.AddPreNode(self.c)
        self.graph.UpdateAdjacencyMatrix()

    def test_create_subgraph_from_nodes(self):
        """Should create a sub-graph from selected nodes."""
        subgraph = self.graph.create_subgraph_from_nodes(
            [self.a, self.b], name="Input Layer"
        )

        assert subgraph is not None
        assert subgraph.graph_name == "Input Layer"
        assert len(subgraph.nodes) == 2
        assert self.a in subgraph.nodes
        assert self.b in subgraph.nodes
        assert subgraph.parent_graph is self.graph
        assert subgraph in self.graph.sub_graphs

    def test_subgraph_inherits_connections(self):
        """Sub-graph should preserve node connections."""
        subgraph = self.graph.create_subgraph_from_nodes(
            [self.a, self.b, self.c], name="Test"
        )

        # Node c should still have predecessors a and b
        c_in_subgraph = next(n for n in subgraph.nodes if n.name == "c")
        assert len(c_in_subgraph.predecessors) == 2

    def test_subgraph_starting_nodes_detected(self):
        """Sub-graph should auto-detect starting nodes."""
        subgraph = self.graph.create_subgraph_from_nodes(
            [self.a, self.b, self.c], name="Test"
        )

        # a and b have no predecessors within the subgraph
        assert self.a in subgraph.starting_nodes
        assert self.b in subgraph.starting_nodes
        assert self.c not in subgraph.starting_nodes

    def test_prevent_duplicate_subgraph(self):
        """Should prevent creating duplicate sub-graphs with same nodes."""
        self.graph.create_subgraph_from_nodes([self.a, self.b], name="First")

        with pytest.raises(ValueError, match="identical nodes already exists"):
            self.graph.create_subgraph_from_nodes([self.a, self.b], name="Second")

    def test_empty_nodes_returns_none(self):
        """Creating sub-graph with no nodes should return None."""
        result = self.graph.create_subgraph_from_nodes([], name="Empty")
        assert result is None

    def test_node_not_in_graph_raises(self):
        """Should raise if node is not in the graph."""
        other_node = ContainerNode("other", value=99)

        with pytest.raises(ValueError, match="not in this graph"):
            self.graph.create_subgraph_from_nodes([other_node], name="Bad")


class TestSubGraphRemoval:
    """Test sub-graph removal."""

    def setup_method(self):
        """Create a graph with sub-graphs."""
        self.graph = Graph()
        self.graph.set_as_mother_graph()

        self.a = ContainerNode("a", value=1)
        self.b = ContainerNode("b", value=2)
        self.graph.AddNode(self.a, self.b)

        self.subgraph = self.graph.create_subgraph_from_nodes(
            [self.a, self.b], name="Test"
        )

    def test_remove_subgraph(self):
        """Should remove sub-graph but keep nodes in parent."""
        result = self.graph.remove_subgraph(self.subgraph)

        assert result is True
        assert self.subgraph not in self.graph.sub_graphs
        assert self.subgraph.parent_graph is None
        # Nodes should still be in parent graph
        assert self.a in self.graph.nodes
        assert self.b in self.graph.nodes

    def test_remove_nonexistent_subgraph(self):
        """Removing non-existent sub-graph should return False."""
        other_subgraph = Graph(name="Other")
        result = self.graph.remove_subgraph(other_subgraph)
        assert result is False


class TestSubGraphQueries:
    """Test sub-graph query methods."""

    def setup_method(self):
        """Create a graph with nested sub-graphs."""
        self.graph = Graph()
        self.graph.set_as_mother_graph()

        self.a = ContainerNode("a", value=1)
        self.b = ContainerNode("b", value=2)
        self.c = ContainerNode("c", value=3)
        self.graph.AddNode(self.a, self.b, self.c)

        self.sub1 = self.graph.create_subgraph_from_nodes([self.a, self.b], name="Sub1")
        self.sub2 = self.graph.create_subgraph_from_nodes([self.c], name="Sub2")

    def test_get_all_subgraphs(self):
        """Should return all sub-graphs."""
        all_subs = self.graph.get_all_subgraphs()
        assert len(all_subs) == 2
        assert self.sub1 in all_subs
        assert self.sub2 in all_subs

    def test_find_subgraph_by_id(self):
        """Should find sub-graph by ID."""
        found = self.graph.find_subgraph_by_id(self.sub1.graph_id)
        assert found is self.sub1

    def test_find_subgraph_by_name(self):
        """Should find sub-graph by name."""
        found = self.graph.find_subgraph_by_name("Sub2")
        assert found is self.sub2

    def test_get_node_subgraphs(self):
        """Should find all sub-graphs containing a node."""
        subgraphs = self.graph.get_node_subgraphs(self.a)
        assert len(subgraphs) == 1
        assert self.sub1 in subgraphs


class TestSubGraphSerialization:
    """Test sub-graph metadata serialization."""

    def setup_method(self):
        """Create a graph with sub-graphs."""
        self.graph = Graph(name="Test Mother")
        self.graph.set_as_mother_graph()

        self.a = ContainerNode("a", value=1)
        self.b = ContainerNode("b", value=2)
        self.c = AdditionNode("c")
        self.graph.AddNode(self.a, self.b, self.c)

        self.c.AddPreNode(self.a)
        self.c.AddPreNode(self.b)
        self.graph.UpdateAdjacencyMatrix()

        self.subgraph = self.graph.create_subgraph_from_nodes(
            [self.a, self.b], name="Inputs"
        )

    def test_get_subgraph_metadata(self):
        """Should serialize sub-graph metadata."""
        meta = self.subgraph.get_subgraph_metadata()

        assert meta["graph_id"] == self.subgraph.graph_id
        assert meta["graph_name"] == "Inputs"
        assert meta["graph_color"] == self.subgraph.graph_color
        assert len(meta["node_ids"]) == 2
        assert self.a.id in meta["node_ids"]
        assert self.b.id in meta["node_ids"]

    def test_restore_subgraph_from_metadata(self):
        """Should restore sub-graph from metadata."""
        meta = self.subgraph.get_subgraph_metadata()

        # Create a new graph and add the same nodes
        new_graph = Graph(name="Restored")
        new_a = ContainerNode("a", value=1)
        new_b = ContainerNode("b", value=2)
        new_graph.AddNode(new_a, new_b)

        # Build id map
        id_map = {new_a.id: new_a, new_b.id: new_b}
        # Also map original IDs
        id_map[self.a.id] = new_a
        id_map[self.b.id] = new_b

        # Clear sub_graphs before restore (restore appends)
        new_graph.sub_graphs = []

        # Restore
        restored = new_graph.restore_subgraph_from_metadata(meta, id_map)

        assert restored is not None
        assert restored.graph_name == "Inputs"
        assert len(restored.nodes) == 2


class TestCGJsonIOMultiGraph:
    """Test CGJsonIO save/load with multi-graph support."""

    def test_save_load_preserves_subgraphs(self):
        """Saving and loading should preserve sub-graph structure."""
        # Create graph with sub-graphs
        graph = Graph(name="Original")
        graph.set_as_mother_graph()

        a = ContainerNode("a", value=1)
        b = ContainerNode("b", value=2)
        c = AdditionNode("c")
        graph.AddNode(a, b, c)

        c.AddPreNode(a)
        c.AddPreNode(b)
        graph.UpdateAdjacencyMatrix()

        graph.create_subgraph_from_nodes([a, b], name="Inputs")

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".cgjson", delete=False) as f:
            temp_path = f.name

        try:
            CGJsonIO.save(graph, temp_path, compress=False)

            # Load back
            loaded_graph = CGJsonIO.load(temp_path)

            # Verify graph identity
            assert loaded_graph.graph_name == "Original"
            assert loaded_graph.is_mother_graph is True

            # Verify sub-graphs
            assert len(loaded_graph.sub_graphs) == 1
            loaded_sub = loaded_graph.sub_graphs[0]
            assert loaded_sub.graph_name == "Inputs"
            assert len(loaded_sub.nodes) == 2

        finally:
            os.unlink(temp_path)

    def test_backward_compatibility(self):
        """Loading old format without sub-graphs should work."""
        # Create old-format JSON
        old_format = {
            "metadata": {"format": "CGJSON", "version": 1},
            "nodes": [
                {
                    "id": "a",
                    "type": "ContainerNode",
                    "name": "a",
                    "attrs": {"value": 1},
                },
            ],
            "edges": [],
            "graph": {
                "starting_nodes": [],
                "stopping_nodes": [],
                "manual_processing_sequence": None,
                # No graph_id, graph_name, sub_graphs
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cgjson", delete=False) as f:
            json.dump(old_format, f)
            temp_path = f.name

        try:
            loaded = CGJsonIO.load(temp_path)

            # Should load without errors
            assert len(loaded.nodes) == 1
            assert loaded.sub_graphs == []  # Empty, not None

        finally:
            os.unlink(temp_path)


class TestProcessingQueue:
    """Test processing queue functionality (Phase 2)."""

    def test_add_to_queue(self):
        """Can add graph+iterations to queue."""
        from ComputationalGraphs.GUI.graph_runner import GraphRunner

        g = Graph(name="Test Graph")
        runner = GraphRunner()
        runner.set_graph(g)

        runner.add_to_queue(g, 100)

        queue = runner.get_queue()
        assert len(queue) == 1
        assert queue[0] == (g, 100)

    def test_add_multiple_to_queue(self):
        """Can add multiple items to queue."""
        from ComputationalGraphs.GUI.graph_runner import GraphRunner

        g1 = Graph(name="Graph A")
        g2 = Graph(name="Graph B")
        runner = GraphRunner()

        runner.add_to_queue(g1, 100)
        runner.add_to_queue(g2, 50)
        runner.add_to_queue(g1, 25)

        queue = runner.get_queue()
        assert len(queue) == 3
        assert queue[0] == (g1, 100)
        assert queue[1] == (g2, 50)
        assert queue[2] == (g1, 25)

    def test_clear_queue(self):
        """Can clear the processing queue."""
        from ComputationalGraphs.GUI.graph_runner import GraphRunner

        g = Graph(name="Test Graph")
        runner = GraphRunner()

        runner.add_to_queue(g, 100)
        runner.add_to_queue(g, 50)
        assert len(runner.get_queue()) == 2

        runner.clear_queue()
        assert len(runner.get_queue()) == 0


class TestPerGraphSnapshots:
    """Test per-graph snapshot functionality (Phase 2)."""

    def test_save_snapshot_for_graph(self):
        """Can save snapshot for specific graph."""
        from ComputationalGraphs.GUI.graph_runner import GraphRunner

        g = Graph(name="Test Graph")
        a = ContainerNode("a", value=5)
        b = ContainerNode("b", value=10)
        g.AddNode(a, b)

        runner = GraphRunner()
        runner.set_graph(g)
        runner.save_graph_snapshot_for(g)

        # Modify values
        a.value = 99
        b.value = 99

        # Restore snapshot
        runner.restore_graph_snapshot_for(g)
        assert a.value == 5
        assert b.value == 10

    def test_separate_snapshots_per_graph(self):
        """Snapshots are kept separate per graph."""
        from ComputationalGraphs.GUI.graph_runner import GraphRunner

        g1 = Graph(name="Graph A")
        a1 = ContainerNode("a1", value=1)
        g1.AddNode(a1)

        g2 = Graph(name="Graph B")
        a2 = ContainerNode("a2", value=100)
        g2.AddNode(a2)

        runner = GraphRunner()

        # Save snapshots for both
        runner.save_graph_snapshot_for(g1)
        runner.save_graph_snapshot_for(g2)

        # Modify both
        a1.value = 999
        a2.value = 999

        # Restore only g1
        runner.restore_graph_snapshot_for(g1)
        assert a1.value == 1
        assert a2.value == 999  # Still modified

        # Restore g2
        runner.restore_graph_snapshot_for(g2)
        assert a2.value == 100


class TestSubGraphFiltering:
    """Test sub-graph filtering for plot selection (Phase 2)."""

    def test_nodes_assigned_to_subgraph(self):
        """Nodes know which subgraph they belong to."""
        g = Graph(name="Main")

        # Create nodes
        a = ContainerNode("a", value=1)
        b = ContainerNode("b", value=2)
        c = AdditionNode("c")
        c.AddPreNode(a, b)

        g.AddNode(a, b, c)

        # Create subgraph from a, b
        sub = g.create_subgraph_from_nodes([a, b], "Inputs")

        # Check subgraph assignment
        assert a.sub_graph_id == sub.graph_id
        assert b.sub_graph_id == sub.graph_id
        assert c.sub_graph_id is None  # Not in any subgraph

    def test_filter_nodes_by_subgraph(self):
        """Can filter nodes by subgraph membership."""
        g = Graph(name="Main")

        a = ContainerNode("a", value=1)
        b = ContainerNode("b", value=2)
        c = AdditionNode("c")
        c.AddPreNode(a, b)
        d = ContainerNode("d", value=5)

        g.AddNode(a, b, c, d)

        # Create subgraph from a, b
        sub = g.create_subgraph_from_nodes([a, b], "Inputs")

        # Filter nodes in subgraph
        sub_nodes = [n for n in g.nodes if n.sub_graph_id == sub.graph_id]
        assert len(sub_nodes) == 2
        assert a in sub_nodes
        assert b in sub_nodes

        # Filter nodes NOT in any subgraph
        main_only = [n for n in g.nodes if n.sub_graph_id is None]
        assert len(main_only) == 2
        assert c in main_only
        assert d in main_only


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
