"""
SwallowNodeCommand - Undoable command for "swallowing" nodes.

Swallowing a node removes it from the graph while connecting all its
predecessors to all its successors, preserving the data flow paths.

Example: a -> b -> c
After swallowing b: a -> c
"""

from PyQt6.QtGui import QUndoCommand


class SwallowNodeCommand(QUndoCommand):
    """Command to swallow (remove while reconnecting) nodes.

    When a node is swallowed:
    1. All its predecessors get connected to all its successors
    2. The node is removed from the graph
    3. Original connections are stored for undo
    """

    def __init__(self, canvas, graph, node_items, description="Swallow Node"):
        if len(node_items) > 1:
            description = f"Swallow {len(node_items)} Nodes"
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph

        # Store node data for restoration: (node, x, y, manual_color, predecessors)
        self.swallowed_nodes = []
        # Store original edges that will be removed: (source_node, target_node)
        self.removed_edges = []
        # Store new edges that will be created: (source_node, target_node)
        self.created_edges = []

        # Build successor map once and collect nodes being swallowed
        successor_map = graph.BuildSuccessorMap()
        nodes_being_swallowed = {item.node for item in node_items}

        # First pass: collect node data and removed edges
        for node_item in node_items:
            self._collect_node_data(node_item, successor_map)

        # Second pass: compute bypass edges with transitive closure
        self._compute_bypass_edges(successor_map, nodes_being_swallowed)

    def _collect_node_data(self, node_item, successor_map):
        """Collect data for a single node being swallowed."""
        node = node_item.node
        pos = node_item.pos()
        manual_color = getattr(node_item, "manual_color", None)

        # Get predecessors and successors
        preds = list(node.predecessors) if hasattr(node, "predecessors") else []
        successors = successor_map.get(node, [])

        # Store node data with its original predecessors
        self.swallowed_nodes.append(
            (node, pos.x(), pos.y(), manual_color, preds[:])
        )

        # Store edges from predecessors to this node (to be removed)
        for pred in preds:
            edge_tuple = (pred, node)
            if edge_tuple not in self.removed_edges:
                self.removed_edges.append(edge_tuple)

        # Store edges from this node to successors (to be removed)
        for succ in successors:
            edge_tuple = (node, succ)
            if edge_tuple not in self.removed_edges:
                self.removed_edges.append(edge_tuple)

    def _compute_bypass_edges(self, successor_map, nodes_being_swallowed):
        """Compute bypass edges handling chains of swallowed nodes."""
        # Find all external predecessors (nodes not being swallowed)
        external_preds = set()
        for node, _, _, _, preds in self.swallowed_nodes:
            for pred in preds:
                if pred not in nodes_being_swallowed:
                    external_preds.add(pred)

        # Find all external successors (nodes not being swallowed)
        external_succs = set()
        for node, _, _, _, _ in self.swallowed_nodes:
            for succ in successor_map.get(node, []):
                if succ not in nodes_being_swallowed:
                    external_succs.add(succ)

        # Connect each external predecessor to each external successor
        for pred in external_preds:
            for succ in external_succs:
                edge_tuple = (pred, succ)
                if pred != succ and edge_tuple not in self.created_edges:
                    if not self._edge_exists(pred, succ):
                        self.created_edges.append(edge_tuple)

    def _edge_exists(self, src, tgt):
        """Check if an edge already exists between src and tgt."""
        return src in getattr(tgt, 'predecessors', [])

    def redo(self):
        """Swallow the nodes: create new edges, then remove nodes."""
        # First, create the new bypass edges
        for src, tgt in self.created_edges:
            self._add_edge(src, tgt)
        
        # Then remove the swallowed nodes (this also removes their edges)
        for node, x, y, manual_color, predecessors in self.swallowed_nodes:
            self._remove_node(node)

    def undo(self):
        """Restore the swallowed nodes and original connections."""
        # First, remove the bypass edges we created
        for src, tgt in self.created_edges:
            self._remove_edge(src, tgt)
        
        # Restore the swallowed nodes
        for node, x, y, manual_color, predecessors in self.swallowed_nodes:
            self._restore_node(node, x, y, manual_color)
        
        # Restore the original edges
        for src, tgt in self.removed_edges:
            self._restore_edge(src, tgt)

    def _add_edge(self, src, tgt):
        """Add an edge between two nodes."""
        # Check both nodes exist in canvas
        if src not in self.canvas.node_items or tgt not in self.canvas.node_items:
            return
        
        # Check edge doesn't already exist visually
        for edge in self.canvas.edge_items:
            try:
                if edge.source_node.node == src and edge.target_node.node == tgt:
                    return  # Already exists
            except Exception:
                pass
        
        # Add edge (this also connects in graph)
        self.canvas.add_edge_item(src, tgt)

    def _remove_edge(self, src, tgt):
        """Remove an edge from graph and canvas."""
        # Find and remove the visual edge
        for edge in list(self.canvas.edge_items):
            try:
                if edge.source_node.node == src and edge.target_node.node == tgt:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                    break
            except Exception:
                pass
        
        # Disconnect in graph
        try:
            self.graph.DisconnectPreNode(tgt, src)
        except Exception:
            pass

    def _remove_node(self, node):
        """Remove a node from graph and canvas."""
        # First remove all edges connected to this node
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
        
        # Remove from graph
        if node in self.graph.nodes:
            try:
                self.graph.RemoveNode(node)
            except Exception:
                try:
                    self.graph.nodes.remove(node)
                except Exception:
                    pass

    def _restore_node(self, node, x, y, manual_color):
        """Restore a node to graph and canvas."""
        # Add back to graph
        if node not in self.graph.nodes:
            self.graph.AddNode(node)
        
        # Add back to canvas
        if node not in self.canvas.node_items:
            node_item = self.canvas.add_node_item(node, x, y)
            if manual_color is not None and node_item is not None:
                try:
                    node_item.set_manual_color(manual_color)
                except Exception:
                    node_item.manual_color = manual_color
                    node_item.update()

    def _restore_edge(self, src, tgt):
        """Restore an edge to graph and canvas."""
        # Check both nodes exist in canvas
        if src not in self.canvas.node_items or tgt not in self.canvas.node_items:
            return
        
        # Check edge doesn't already exist
        for edge in self.canvas.edge_items:
            try:
                if edge.source_node.node == src and edge.target_node.node == tgt:
                    return  # Already exists
            except Exception:
                pass
        
        # Add edge (this also connects in graph)
        self.canvas.add_edge_item(src, tgt)
