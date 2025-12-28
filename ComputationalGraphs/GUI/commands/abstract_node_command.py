"""
AbstractNodeCommand - Undoable command for abstracting nodes.

Abstracting nodes groups disjoint nodes (a, b, c) that share the same
predecessors and successors into a single AbstractNode that processes them
in parallel.
"""

import math

from PyQt6.QtGui import QUndoCommand


class AbstractNodeCommand(QUndoCommand):
    """Command to abstract a set of disjoint nodes into an AbstractNode.

    When nodes are abstracted:
    1. A new AbstractNode is created containing the disjoint nodes
    2. Shared predecessors connect to the AbstractNode
    3. Shared successors connect from the AbstractNode
    4. Original nodes are removed from the graph (but kept in AbstractNode)
    """

    def __init__(self, canvas, graph, node_items, description="Abstract Nodes"):
        if len(node_items) > 1:
            description = f"Abstract {len(node_items)} Nodes"
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph

        # Store original node data for undo: (node, x, y, manual_color)
        self.original_nodes = []
        # Store original edges: (source_node, target_node)
        self.original_edges = []
        # The abstract node that will be created
        self.abstract_node = None
        # Position for the abstract node (center of original nodes)
        self.abstract_x = 0
        self.abstract_y = 0

        # Collect node data
        nodes = [item.node for item in node_items]
        self.nodes_to_abstract = nodes

        # Calculate center position for abstract node
        total_x = 0
        total_y = 0
        for node_item in node_items:
            pos = node_item.pos()
            total_x += pos.x()
            total_y += pos.y()
            manual_color = getattr(node_item, "manual_color", None)
            self.original_nodes.append((node_item.node, pos.x(), pos.y(), manual_color))
        self.abstract_x = total_x / len(node_items)
        self.abstract_y = total_y / len(node_items)

        # Collect all edges involving these nodes
        successor_map = graph.BuildSuccessorMap()

        for node in nodes:
            # Incoming edges
            for pred in node.predecessors:
                edge_tuple = (pred, node)
                if edge_tuple not in self.original_edges:
                    self.original_edges.append(edge_tuple)
            # Outgoing edges
            for succ in successor_map.get(node, []):
                edge_tuple = (node, succ)
                if edge_tuple not in self.original_edges:
                    self.original_edges.append(edge_tuple)

    def redo(self):
        """Abstract the nodes: create AbstractNode, update connections."""
        # First, remove visual edges for all original nodes
        for src, tgt in self.original_edges:
            self._remove_visual_edge(src, tgt)

        # Remove visual node items (but don't remove from graph yet)
        for node, x, y, manual_color in self.original_nodes:
            self._remove_visual_node(node)

        # Use Graph.AbstractNodes to do the actual abstraction
        self.abstract_node = self.graph.AbstractNodes(self.nodes_to_abstract)

        if self.abstract_node:
            # Add visual representation for abstract node
            self._add_visual_node(self.abstract_node, self.abstract_x, self.abstract_y)

            # Add visual edges for abstract node's connections
            for pred in self.abstract_node.predecessors:
                if pred in self.canvas.node_items:
                    self._add_visual_edge(pred, self.abstract_node)

            successor_map = self.graph.BuildSuccessorMap()
            for succ in successor_map.get(self.abstract_node, []):
                if succ in self.canvas.node_items:
                    self._add_visual_edge(self.abstract_node, succ)

    def undo(self):
        """Expand: restore original nodes and connections."""
        if self.abstract_node is None:
            return

        # Remove visual edges from abstract node
        if self.abstract_node in self.canvas.node_items:
            node_item = self.canvas.node_items[self.abstract_node]
            for edge in list(node_item.edges[:]):
                try:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                except Exception:
                    pass

        # Remove abstract node visual
        self._remove_visual_node(self.abstract_node)

        # Use Graph.ExpandAbstractNode to restore nodes
        self.graph.ExpandAbstractNode(self.abstract_node)

        # Restore visual nodes at original positions
        for node, x, y, manual_color in self.original_nodes:
            if node in self.graph.nodes:
                node_item = self._add_visual_node(node, x, y)
                if manual_color is not None and node_item is not None:
                    try:
                        node_item.set_manual_color(manual_color)
                    except Exception:
                        node_item.manual_color = manual_color
                        node_item.update()

        # Restore visual edges
        for src, tgt in self.original_edges:
            if src in self.canvas.node_items and tgt in self.canvas.node_items:
                self._add_visual_edge(src, tgt)

        self.abstract_node = None

    def _add_visual_node(self, node, x, y):
        """Add a node to the canvas visually."""
        if node not in self.canvas.node_items:
            return self.canvas.add_node_item(node, x, y)
        return self.canvas.node_items.get(node)

    def _remove_visual_node(self, node):
        """Remove a node from the canvas visually (not from graph)."""
        if node in self.canvas.node_items:
            node_item = self.canvas.node_items[node]
            # Remove all edges connected to this node
            for edge in list(node_item.edges[:]):
                try:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                except Exception:
                    pass
            # Remove the node item from scene
            try:
                self.canvas.scene.removeItem(node_item)
            except Exception:
                pass
            del self.canvas.node_items[node]

    def _add_visual_edge(self, src, tgt):
        """Add an edge between two nodes visually."""
        if src not in self.canvas.node_items or tgt not in self.canvas.node_items:
            return

        # Check edge doesn't already exist
        for edge in self.canvas.edge_items:
            try:
                if edge.source_node.node == src and edge.target_node.node == tgt:
                    return
            except Exception:
                pass

        # Add edge visually (also connects in graph if not connected)
        self.canvas.add_edge_item(src, tgt)

    def _remove_visual_edge(self, src, tgt):
        """Remove an edge visually."""
        for edge in list(self.canvas.edge_items):
            try:
                if edge.source_node.node == src and edge.target_node.node == tgt:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                    break
            except Exception:
                pass


class ExpandAbstractNodeCommand(QUndoCommand):
    """Command to expand an AbstractNode back to its original disjoint nodes."""

    def __init__(self, canvas, graph, node_item, description="Expand Abstract Node"):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.node_item = node_item
        self.abstract_node = node_item.node
        self.abstract_x = node_item.pos().x()
        self.abstract_y = node_item.pos().y()
        self.abstract_color = getattr(node_item, "manual_color", None)

        # Store internal nodes for positioning after expand
        self.internal_nodes = list(self.abstract_node.nodes)

        # Store edges to/from abstract node
        self.abstract_edges = []
        successor_map = graph.BuildSuccessorMap()
        for pred in self.abstract_node.predecessors:
            self.abstract_edges.append((pred, self.abstract_node))
        for succ in successor_map.get(self.abstract_node, []):
            self.abstract_edges.append((self.abstract_node, succ))

        # Restored nodes will be stored here after redo
        self.restored_nodes = []

    def redo(self):
        """Expand the abstract node."""
        # Remove visual edges from abstract node
        if self.abstract_node in self.canvas.node_items:
            node_item = self.canvas.node_items[self.abstract_node]
            for edge in list(node_item.edges[:]):
                try:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                except Exception:
                    pass

        # Remove abstract node visual
        self._remove_visual_node(self.abstract_node)

        # Expand in graph
        self.restored_nodes = self.graph.ExpandAbstractNode(self.abstract_node) or []

        # Add visual nodes - spread them out in a circular pattern from center
        n = len(self.restored_nodes)
        for i, node in enumerate(self.restored_nodes):
            if node in self.graph.nodes:
                # Position nodes in a circle around the abstract node position
                if n == 1:
                    x, y = self.abstract_x, self.abstract_y
                else:
                    angle = 2 * math.pi * i / n
                    radius = 80
                    x = self.abstract_x + radius * math.cos(angle)
                    y = self.abstract_y + radius * math.sin(angle)
                self._add_visual_node(node, x, y)

        # Add visual edges for restored nodes
        successor_map = self.graph.BuildSuccessorMap()
        for node in self.restored_nodes:
            for pred in node.predecessors:
                if pred in self.canvas.node_items:
                    self._add_visual_edge(pred, node)
            for succ in successor_map.get(node, []):
                if succ in self.canvas.node_items:
                    self._add_visual_edge(node, succ)

    def undo(self):
        """Re-abstract the nodes."""
        if not self.restored_nodes:
            return

        # Remove visual representation of restored nodes
        for node in self.restored_nodes:
            self._remove_visual_node(node)

        # Re-abstract the nodes
        self.abstract_node = self.graph.AbstractNodes(self.internal_nodes)

        if self.abstract_node:
            # Add visual representation
            node_item = self._add_visual_node(
                self.abstract_node, self.abstract_x, self.abstract_y
            )
            if self.abstract_color is not None and node_item is not None:
                try:
                    node_item.set_manual_color(self.abstract_color)
                except Exception:
                    pass

            # Add visual edges
            for pred in self.abstract_node.predecessors:
                if pred in self.canvas.node_items:
                    self._add_visual_edge(pred, self.abstract_node)

            successor_map = self.graph.BuildSuccessorMap()
            for succ in successor_map.get(self.abstract_node, []):
                if succ in self.canvas.node_items:
                    self._add_visual_edge(self.abstract_node, succ)

    def _add_visual_node(self, node, x, y):
        """Add a node to the canvas visually."""
        if node not in self.canvas.node_items:
            return self.canvas.add_node_item(node, x, y)
        return self.canvas.node_items.get(node)

    def _remove_visual_node(self, node):
        """Remove a node from the canvas visually."""
        if node in self.canvas.node_items:
            node_item = self.canvas.node_items[node]
            for edge in list(node_item.edges[:]):
                try:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                except Exception:
                    pass
            try:
                self.canvas.scene.removeItem(node_item)
            except Exception:
                pass
            del self.canvas.node_items[node]

    def _add_visual_edge(self, src, tgt):
        """Add an edge between two nodes visually."""
        if src not in self.canvas.node_items or tgt not in self.canvas.node_items:
            return
        for edge in self.canvas.edge_items:
            try:
                if edge.source_node.node == src and edge.target_node.node == tgt:
                    return
            except Exception:
                pass
        self.canvas.add_edge_item(src, tgt)
