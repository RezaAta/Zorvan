"""
GraphLayoutController - Manages graph layout algorithm application.

Extracted from MainWindow as part of Clean Code refactoring.
Handles layout algorithm selection, execution, and position application.
"""
from typing import TYPE_CHECKING, Dict, Tuple

from PyQt6.QtWidgets import QMessageBox

from .. import layouts as layout_algorithms

if TYPE_CHECKING:
    from ..main_window import MainWindow


class GraphLayoutController:
    """Controller for applying graph layout algorithms."""
    
    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window
    
    def update_layout_status_label(self):
        """Update the layout status label to show library availability."""
        label = self.main_window.layout_status_label
        
        if layout_algorithms.is_grandalf_available():
            label.setText("✓ grandalf available (Sugiyama)")
            label.setStyleSheet("color: #4CAF50;")
        elif layout_algorithms.is_networkx_available():
            label.setText("⚠ Using NetworkX fallback")
            label.setStyleSheet("color: #FFC107;")
        else:
            label.setText("⚠ No layout library found")
            label.setStyleSheet("color: #f44336;")
    
    def apply_graph_layout(self, layout_type: str, spacing: int = None):
        """Apply a graph layout algorithm to the current graph.
        
        Args:
            layout_type: One of 'sugiyama', 'tree', 'mlp_layered', or 'mlp_layout'
            spacing: Optional override for node spacing (uses UI spin value if None)
        """
        mw = self.main_window
        
        if not mw.graph or not mw.graph.nodes:
            mw.status_bar.showMessage("No graph to layout")
            return
        
        # Get layout direction from combo
        direction = 'LR' if mw.layout_direction_combo.currentIndex() == 0 else 'TB'
        
        # Get node spacing from spin box or override
        if spacing is not None:
            node_spacing = spacing
        else:
            node_spacing = mw.layout_spacing_spin.value()
        layer_spacing = int(node_spacing * 1.5)  # Proportional
        
        # Build predecessors lookup function
        def get_predecessors(node):
            return getattr(node, 'predecessors', [])
        
        # Apply the selected layout algorithm
        try:
            positions = self._compute_layout(
                layout_type, mw.graph.nodes, get_predecessors,
                node_spacing, layer_spacing, direction
            )
            
            if positions is None:
                mw.status_bar.showMessage(f"Unknown layout type: {layout_type}")
                return
            
            # Apply positions to nodes and update canvas
            self._apply_layout_positions(positions)
            
            # Apply ANN colors for neural network layouts
            if layout_type in ('mlp_layered', 'mlp_layout'):
                mw.canvas.apply_ann_colors()
            
            mw.status_bar.showMessage(
                f"Applied {layout_type} layout to {len(positions)} nodes"
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(
                mw,
                "Layout Error",
                f"Failed to apply {layout_type} layout:\n{str(e)}"
            )
    
    def _compute_layout(self, layout_type: str, nodes, get_predecessors,
                        node_spacing: int, layer_spacing: int,
                        direction: str) -> Dict[any, Tuple[float, float]]:
        """Compute layout positions using the specified algorithm.
        
        Args:
            layout_type: Layout algorithm name
            nodes: List of graph nodes
            get_predecessors: Function to get predecessors of a node
            node_spacing: Spacing between nodes
            layer_spacing: Spacing between layers
            direction: 'LR' or 'TB'
            
        Returns:
            Dictionary mapping nodes to (x, y) positions, or None if unknown layout type
        """
        if layout_type == 'sugiyama':
            return layout_algorithms.sugiyama_layout(
                nodes,
                get_predecessors,
                node_width=80,
                node_height=80,
                layer_spacing=layer_spacing,
                node_spacing=node_spacing,
                direction=direction
            )
        elif layout_type == 'tree':
            return layout_algorithms.tree_layout(
                nodes,
                get_predecessors,
                node_spacing=node_spacing,
                level_spacing=layer_spacing,
                direction=direction
            )
        elif layout_type == 'mlp_layered':
            return layout_algorithms.mlp_layered_layout(
                nodes,
                get_predecessors,
                node_spacing=node_spacing,
                layer_spacing=layer_spacing,
                direction=direction
            )
        elif layout_type in ('mlp_layout', 'mlp_full'):
            return layout_algorithms.mlp_layout(
                nodes,
                get_predecessors,
                node_spacing=node_spacing,
                layer_spacing=layer_spacing,
                direction=direction
            )
        else:
            return None
    
    def _apply_layout_positions(self, positions: Dict[any, Tuple[float, float]]):
        """Apply computed layout positions to nodes on the canvas.
        
        Args:
            positions: Dictionary mapping nodes to (x, y) tuples
        """
        if not positions:
            return
        
        canvas = self.main_window.canvas
        
        # Center the layout around the origin
        xs = [p[0] for p in positions.values()]
        ys = [p[1] for p in positions.values()]
        center_x = (min(xs) + max(xs)) / 2
        center_y = (min(ys) + max(ys)) / 2
        
        # Apply positions to nodes
        for node, (x, y) in positions.items():
            # Center the layout
            adj_x = x - center_x
            adj_y = y - center_y
            
            # Update node's gui_pos
            node.gui_pos = (adj_x, adj_y)
            
            # Update canvas item if it exists
            if node in canvas.node_items:
                item = canvas.node_items[node]
                item.setPos(adj_x, adj_y)
        
        # Update all edges
        for edge_item in canvas.edge_items:
            try:
                edge_item.update_position()
            except Exception:
                pass
        
        # Update scene rect
        canvas._update_scene_rect()
