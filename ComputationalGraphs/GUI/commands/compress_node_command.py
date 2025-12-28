"""
CompressNodeCommand - Undoable command for compressing nodes.

Compressing nodes combines sequential nodes (a -> b -> c) into a single
CompressedNode that processes them internally in order.
"""

from PyQt6.QtGui import QUndoCommand

from ComputationalGraphs.Nodes.CompressedNode import CompressedNode


class CompressNodeCommand(QUndoCommand):
    """Command to compress a chain of nodes into a CompressedNode.

    When nodes are compressed:
    1. A new CompressedNode is created containing the chain
    2. External predecessors connect to the CompressedNode
    3. External successors connect from the CompressedNode
    4. Original nodes are removed from the graph (but kept in CompressedNode)
    """

    def __init__(self, canvas, graph, node_items, description="Compress Nodes"):
        if len(node_items) > 1:
            description = f"Compress {len(node_items)} Nodes"
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph

        # Store original node data for undo: (node, x, y, manual_color)
        self.original_nodes = []
        # Store original edges: (source_node, target_node)
        self.original_edges = []
        # The compressed node that will be created
        self.compressed_node = None
        # Position for the compressed node (center of original nodes)
        self.compressed_x = 0
        self.compressed_y = 0

        # Collect node data
        nodes = [item.node for item in node_items]
        self.nodes_to_compress = nodes

        # Calculate center position for compressed node
        total_x = 0
        total_y = 0
        for node_item in node_items:
            pos = node_item.pos()
            total_x += pos.x()
            total_y += pos.y()
            manual_color = getattr(node_item, "manual_color", None)
            self.original_nodes.append((node_item.node, pos.x(), pos.y(), manual_color))
        self.compressed_x = total_x / len(node_items)
        self.compressed_y = total_y / len(node_items)

        # Collect all edges involving these nodes
        nodes_set = set(nodes)
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
        """Compress the nodes: create CompressedNode, update connections."""
        # First, remove visual edges for all original nodes
        for src, tgt in self.original_edges:
            self._remove_visual_edge(src, tgt)

        # Remove visual node items (but don't remove from graph yet)
        for node, x, y, manual_color in self.original_nodes:
            self._remove_visual_node(node)

        # Use Graph.CompressNodes to do the actual compression
        self.compressed_node = self.graph.CompressNodes(self.nodes_to_compress)

        if self.compressed_node:
            # Add visual representation for compressed node
            self._add_visual_node(
                self.compressed_node, self.compressed_x, self.compressed_y
            )

            # Add visual edges for compressed node's connections
            for pred in self.compressed_node.predecessors:
                if pred in self.canvas.node_items:
                    self._add_visual_edge(pred, self.compressed_node)

            successor_map = self.graph.BuildSuccessorMap()
            for succ in successor_map.get(self.compressed_node, []):
                if succ in self.canvas.node_items:
                    self._add_visual_edge(self.compressed_node, succ)

    def undo(self):
        """Decompress: restore original nodes and connections."""
        if self.compressed_node is None:
            return

        # Remove visual edges from compressed node
        if self.compressed_node in self.canvas.node_items:
            node_item = self.canvas.node_items[self.compressed_node]
            for edge in list(node_item.edges[:]):
                try:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                except Exception:
                    pass

        # Remove compressed node visual
        self._remove_visual_node(self.compressed_node)

        # Use Graph.DecompressNode to restore nodes
        self.graph.DecompressNode(self.compressed_node, mode="full")

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

        self.compressed_node = None

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


class DecompressNodeCommand(QUndoCommand):
    """Command to decompress a CompressedNode back to its original nodes."""

    def __init__(
        self, canvas, graph, node_item, mode="full", description="Decompress Node"
    ):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.node_item = node_item
        self.compressed_node = node_item.node
        self.mode = mode

        # Store compressed node state for redo
        self.compressed_x = node_item.pos().x()
        self.compressed_y = node_item.pos().y()
        self.compressed_color = getattr(node_item, "manual_color", None)

        # Store internal nodes for positioning after decompress
        self.internal_nodes = list(self.compressed_node.nodes)

        # Store edges to/from compressed node
        self.compressed_edges = []
        successor_map = graph.BuildSuccessorMap()
        for pred in self.compressed_node.predecessors:
            self.compressed_edges.append((pred, self.compressed_node))
        for succ in successor_map.get(self.compressed_node, []):
            self.compressed_edges.append((self.compressed_node, succ))

        # Restored nodes will be stored here after redo
        self.restored_nodes = []

    def redo(self):
        """Decompress the node."""
        # Remove visual edges from compressed node
        if self.compressed_node in self.canvas.node_items:
            node_item = self.canvas.node_items[self.compressed_node]
            for edge in list(node_item.edges[:]):
                try:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                except Exception:
                    pass

        # Remove compressed node visual
        self._remove_visual_node(self.compressed_node)

        # Decompress in graph
        self.restored_nodes = (
            self.graph.DecompressNode(self.compressed_node, mode=self.mode) or []
        )

        # Add visual nodes - spread them out from center
        n = len(self.restored_nodes)
        for i, node in enumerate(self.restored_nodes):
            if node in self.graph.nodes:
                # Position nodes in a line from the compressed node position
                offset = (i - (n - 1) / 2) * 100
                x = self.compressed_x + offset
                y = self.compressed_y
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
        """Re-compress the nodes."""
        if not self.restored_nodes:
            return

        # Remove visual representation of restored nodes
        for node in self.restored_nodes:
            self._remove_visual_node(node)

        # Re-compress the nodes
        self.compressed_node = self.graph.CompressNodes(self.internal_nodes)

        if self.compressed_node:
            # Add visual representation
            node_item = self._add_visual_node(
                self.compressed_node, self.compressed_x, self.compressed_y
            )
            if self.compressed_color is not None and node_item is not None:
                try:
                    node_item.set_manual_color(self.compressed_color)
                except Exception:
                    pass

            # Add visual edges
            for pred in self.compressed_node.predecessors:
                if pred in self.canvas.node_items:
                    self._add_visual_edge(pred, self.compressed_node)

            successor_map = self.graph.BuildSuccessorMap()
            for succ in successor_map.get(self.compressed_node, []):
                if succ in self.canvas.node_items:
                    self._add_visual_edge(self.compressed_node, succ)

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
