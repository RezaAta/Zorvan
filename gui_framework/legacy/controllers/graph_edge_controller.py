"""
GraphEdgeController - Manages edge creation/removal and graph rebuilding.

Extracted from MainWindow as part of Clean Code refactoring.
Handles edge events and graph structure updates.
"""

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from ..main_window import MainWindow


class GraphEdgeController:
    """Controller for edge events and graph structure management."""

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window

    def on_edge_created(self, source_node, target_node):
        """Handle edge creation.

        Args:
            source_node: The source node of the edge
            target_node: The target node of the edge
        """
        mw = self.main_window
        mw.status_bar.showMessage(f"Connected {source_node.name} -> {target_node.name}")

        # Keep adjacency matrix updated
        try:
            if mw.graph:
                mw.graph.UpdateAdjacencyMatrix()
        except Exception:
            pass

        # Reset forward processing controls state if needed
        self._reset_forward_state_if_needed()

    def on_edge_removed(self, source_node, target_node):
        """Handle edge removal.

        Args:
            source_node: The source node of the removed edge
            target_node: The target node of the removed edge
        """
        mw = self.main_window
        mw.status_bar.showMessage(
            f"Disconnected {source_node.name} -> {target_node.name}"
        )

        try:
            if mw.graph:
                mw.graph.UpdateAdjacencyMatrix()
        except Exception:
            pass

        # Reset the graph processor forward state so it reinitializes internal caches
        self._reset_forward_state_if_needed()

    def _reset_forward_state_if_needed(self):
        """Reset forward processing state if processor is in forward mode."""
        mw = self.main_window
        try:
            if hasattr(mw, "graph_runner") and getattr(mw, "graph_runner") is not None:
                processor_type = getattr(mw, "processor_type", None)
                runner_type = getattr(mw.graph_runner, "processor_type", None)

                if processor_type == "forward" or runner_type == "forward":
                    try:
                        mw.graph_runner.reset_processor()
                    except Exception:
                        pass
        except Exception:
            pass

    def rebuild_graph(self):
        """Rebuild the graph from canvas nodes and edges."""
        from zorvan.Core.Graph import Graph

        mw = self.main_window

        # If canvas is empty, confirm with the user before wiping an existing graph
        if not mw.canvas.node_items:
            reply = QMessageBox.question(
                mw,
                "Rebuild Graph",
                "Canvas is empty. Rebuilding will clear the existing graph. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            # Ensure the canvas scene rect includes all created nodes
            try:
                mw.canvas._update_scene_rect()
            except Exception:
                pass
            # Center view on the scene center so large examples are visible immediately
            try:
                center = mw.canvas.scene.sceneRect().center()
                mw.canvas.centerOn(center)
            except Exception:
                pass
            if reply != QMessageBox.StandardButton.Yes:
                mw.status_bar.showMessage("Rebuild cancelled")
                return

        # Preserve starting_nodes, stopping_nodes, and manual sequence before rebuilding
        old_starting_nodes = (
            list(mw.graph.starting_nodes) if hasattr(mw.graph, "starting_nodes") else []
        )
        old_stopping_nodes = (
            list(mw.graph.stopping_nodes) if hasattr(mw.graph, "stopping_nodes") else []
        )
        old_manual_sequence = (
            list(mw.graph.manual_processing_sequence)
            if hasattr(mw.graph, "manual_processing_sequence")
            and mw.graph.manual_processing_sequence
            else None
        )

        # Preserve sub-graphs before rebuilding
        old_sub_graphs = (
            list(mw.graph.sub_graphs) if hasattr(mw.graph, "sub_graphs") else []
        )
        old_graph_id = getattr(mw.graph, "graph_id", None)
        old_graph_name = getattr(mw.graph, "graph_name", "Default Graph")
        old_graph_color = getattr(mw.graph, "graph_color", "#4ECDC4")

        new_graph = Graph()

        # Add all nodes
        for node in mw.canvas.node_items.keys():
            new_graph.AddNode(node)

        # Add edges (connections)
        for edge_item in mw.canvas.edge_items:
            source = edge_item.source_node.node
            target = edge_item.target_node.node

            # Add connection - check if source is not already a predecessor of target
            if source not in target.predecessors:
                target.AddPreNode(source)

        # Update adjacency matrix
        new_graph.UpdateAdjacencyMatrix()

        # Restore starting_nodes, stopping_nodes and manual sequence
        new_graph.starting_nodes = old_starting_nodes
        new_graph.stopping_nodes = old_stopping_nodes
        new_graph.manual_processing_sequence = old_manual_sequence

        # Restore graph identity and sub-graphs
        if old_graph_id:
            new_graph.graph_id = old_graph_id
        new_graph.graph_name = old_graph_name
        new_graph.graph_color = old_graph_color

        # Restore sub-graphs (they reference original node objects, which are preserved)
        for sg in old_sub_graphs:
            # Verify all nodes in subgraph are still in the new graph
            valid_nodes = [n for n in sg.nodes if n in new_graph.nodes]
            if valid_nodes:
                sg.nodes = valid_nodes
                sg.parent_graph = new_graph
                new_graph.sub_graphs.append(sg)
                # Rebuild subgraph adjacency matrix
                sg.UpdateAdjacencyMatrix()

        # Set the graph via the helper to synchronize canvas and runner
        mw.set_graph(new_graph)

        # Update UI state
        try:
            mw.update_starting_nodes_display()
            mw.update_stopping_nodes_display()
        except Exception:
            pass

        mw.status_bar.showMessage("Graph rebuilt from canvas")
