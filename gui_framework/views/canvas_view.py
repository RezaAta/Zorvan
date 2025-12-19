"""
Canvas View - PyQt6 QGraphicsView for rendering computational graphs.

This is the Stage 1 (Rendering) implementation focusing on displaying
nodes and edges from the CanvasViewModel. Interaction will be added in Stage 2.
"""

from typing import Dict, Optional

try:
    from PyQt6.QtCore import Qt, QPointF, QRectF
    from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QFont, QPainterPath
    from PyQt6.QtWidgets import (
        QGraphicsView,
        QGraphicsScene,
        QGraphicsEllipseItem,
        QGraphicsPathItem,
        QGraphicsTextItem,
        QGraphicsItem,
    )
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


if PYQT_AVAILABLE:
    from gui_framework.views.base import BaseView
    from gui_framework.viewmodels.canvas_viewmodel import (
        CanvasViewModel,
        NodeRenderState,
        EdgeRenderState,
    )


    class NodeItemView(QGraphicsEllipseItem):
        """Visual representation of a graph node as a circle."""

        def __init__(self, node_state: NodeRenderState, radius: float = 40):
            """
            Initialize node visual item.

            Args:
                node_state: State data for the node
                radius: Radius of the node circle
            """
            super().__init__(-radius, -radius, radius * 2, radius * 2)
            
            self.node_id = node_state.node_id
            self.radius = radius
            
            # Set position
            self.setPos(node_state.x, node_state.y)
            
            # Set flags
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)  # Stage 1: no interaction
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)  # Stage 1: no selection
            self.setZValue(2)  # Draw above edges
            
            # Set colors based on node type
            if node_state.is_compressed:
                # Gold/amber for compressed nodes
                default_color = QColor(212, 160, 23)
            elif node_state.is_abstract:
                # Purple for abstract nodes
                default_color = QColor(155, 89, 182)
            elif node_state.color:
                # Custom color if set
                default_color = QColor(node_state.color)
            else:
                # Default blue
                default_color = QColor(0, 63, 189)
            
            # Active node highlighting
            if node_state.is_active:
                self.setBrush(QBrush(QColor(100, 180, 255)))  # Bright light blue
            else:
                self.setBrush(QBrush(default_color))
            
            self.setPen(QPen(Qt.GlobalColor.black, 2))
            
            # Create label
            label_text = node_state.name
            if node_state.node_count is not None:
                label_text = f"{node_state.name} [{node_state.node_count}]"
            
            self.label = QGraphicsTextItem(label_text, self)
            font = QFont()
            font.setPointSize(10)
            self.label.setFont(font)
            self.label.setDefaultTextColor(Qt.GlobalColor.white)
            
            # Center label
            label_rect = self.label.boundingRect()
            label_x = -label_rect.width() / 2
            label_y = -label_rect.height() / 2
            self.label.setPos(label_x, label_y)
        
        def update_state(self, node_state: NodeRenderState):
            """
            Update visual appearance from node state.

            Args:
                node_state: Updated state data
            """
            # Update position
            self.setPos(node_state.x, node_state.y)
            
            # Update color
            if node_state.is_active:
                self.setBrush(QBrush(QColor(100, 180, 255)))
            elif node_state.color:
                self.setBrush(QBrush(QColor(node_state.color)))
            elif node_state.is_compressed:
                self.setBrush(QBrush(QColor(212, 160, 23)))
            elif node_state.is_abstract:
                self.setBrush(QBrush(QColor(155, 89, 182)))
            else:
                self.setBrush(QBrush(QColor(0, 63, 189)))
            
            # Update label if needed
            label_text = node_state.name
            if node_state.node_count is not None:
                label_text = f"{node_state.name} [{node_state.node_count}]"
            
            if self.label.toPlainText() != label_text:
                self.label.setPlainText(label_text)
                # Re-center label
                label_rect = self.label.boundingRect()
                label_x = -label_rect.width() / 2
                label_y = -label_rect.height() / 2
                self.label.setPos(label_x, label_y)


    class EdgeItemView(QGraphicsPathItem):
        """Visual representation of an edge connecting two nodes."""

        def __init__(self, edge_state: EdgeRenderState, source_item: NodeItemView, target_item: NodeItemView):
            """
            Initialize edge visual item.

            Args:
                edge_state: State data for the edge
                source_item: Source node visual item
                target_item: Target node visual item
            """
            super().__init__()
            
            self.edge_id = edge_state.edge_id
            self.source_item = source_item
            self.target_item = target_item
            
            # Set visual properties
            self.setPen(QPen(QColor(80, 80, 80), 2))
            self.setZValue(-1)  # Draw behind nodes
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)  # Stage 1: no selection
            
            self.arrow_size = 12
            
            self.update_position()
        
        def update_position(self):
            """Recalculate edge path based on node positions."""
            import math
            
            # Get node positions
            source_pos = self.source_item.scenePos()
            target_pos = self.target_item.scenePos()
            
            # Calculate direction
            dx = target_pos.x() - source_pos.x()
            dy = target_pos.y() - source_pos.y()
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance == 0:
                return  # Nodes at same position
            
            # Normalize direction
            dx_norm = dx / distance
            dy_norm = dy / distance
            
            # Calculate start point (on source node edge)
            source_radius = self.source_item.radius
            start = QPointF(
                source_pos.x() + dx_norm * source_radius,
                source_pos.y() + dy_norm * source_radius,
            )
            
            # Calculate end point (on target node edge, with arrow space)
            target_radius = self.target_item.radius
            end = QPointF(
                target_pos.x() - dx_norm * (target_radius + self.arrow_size),
                target_pos.y() - dy_norm * (target_radius + self.arrow_size),
            )
            
            # Create bezier curve path
            path = QPainterPath()
            path.moveTo(start)
            
            # Control points for smooth curve
            ctrl_offset = distance * 0.25
            perp_x = -dy_norm * ctrl_offset * 0.3
            perp_y = dx_norm * ctrl_offset * 0.3
            
            ctrl1 = QPointF(
                start.x() + dx_norm * ctrl_offset + perp_x,
                start.y() + dy_norm * ctrl_offset + perp_y,
            )
            ctrl2 = QPointF(
                end.x() - dx_norm * ctrl_offset - perp_x,
                end.y() - dy_norm * ctrl_offset - perp_y,
            )
            
            path.cubicTo(ctrl1, ctrl2, end)
            
            # Add arrowhead
            angle = math.atan2(dy, dx)
            arrow_p1 = QPointF(
                end.x() - self.arrow_size * math.cos(angle - math.pi / 6),
                end.y() - self.arrow_size * math.sin(angle - math.pi / 6),
            )
            arrow_p2 = QPointF(
                end.x() - self.arrow_size * math.cos(angle + math.pi / 6),
                end.y() - self.arrow_size * math.sin(angle + math.pi / 6),
            )
            
            path.moveTo(end)
            path.lineTo(arrow_p1)
            path.moveTo(end)
            path.lineTo(arrow_p2)
            
            self.setPath(path)


    class CanvasView(BaseView):
        """
        PyQt6 view for the computational graph canvas.

        Stage 1 (Rendering): Displays nodes and edges from ViewModel.
        Supports zoom/pan but no interaction yet.
        """

        def __init__(self, viewmodel: CanvasViewModel, parent=None):
            """
            Initialize canvas view.

            Args:
                viewmodel: Canvas view-model
                parent: Optional parent widget
            """
            super().__init__(viewmodel, parent)
            
            # Create graphics view and scene
            self.scene = QGraphicsScene()
            self.view = QGraphicsView(self.scene)
            self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)  # Stage 1: no drag
            
            # Node and edge item tracking
            self._node_items: Dict[str, NodeItemView] = {}
            self._edge_items: Dict[str, EdgeItemView] = {}
            
            self._setup_ui()
        
        def _setup_ui(self):
            """Setup the canvas UI."""
            # Use view as the main widget (this is a wrapper)
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.view)
        
        def _bind_viewmodel(self):
            """Bind to viewmodel properties."""
            self._viewmodel.observe_property("nodes_changed", self._on_nodes_changed)
            self._viewmodel.observe_property("edges_changed", self._on_edges_changed)
            self._viewmodel.observe_property("viewport_changed", self._on_viewport_changed)
        
        def _on_nodes_changed(self, old_value, new_value):
            """Handle nodes changed event."""
            self._render_nodes()
        
        def _on_edges_changed(self, old_value, new_value):
            """Handle edges changed event."""
            self._render_edges()
        
        def _on_viewport_changed(self, old_value, new_value):
            """Handle viewport changed event."""
            viewport = self._viewmodel.get_viewport()
            
            # Apply zoom
            self.view.resetTransform()
            self.view.scale(viewport.zoom_level, viewport.zoom_level)
            
            # Apply pan
            self.view.centerOn(viewport.center_x, viewport.center_y)
        
        def _render_nodes(self):
            """Render all nodes from viewmodel."""
            nodes = self._viewmodel.get_nodes()
            
            # Get current node IDs
            current_ids = {n.node_id for n in nodes}
            existing_ids = set(self._node_items.keys())
            
            # Remove nodes that no longer exist
            for node_id in existing_ids - current_ids:
                item = self._node_items.pop(node_id)
                self.scene.removeItem(item)
            
            # Add or update nodes
            for node_state in nodes:
                if node_state.node_id in self._node_items:
                    # Update existing node
                    self._node_items[node_state.node_id].update_state(node_state)
                else:
                    # Create new node
                    item = NodeItemView(node_state)
                    self.scene.addItem(item)
                    self._node_items[node_state.node_id] = item
        
        def _render_edges(self):
            """Render all edges from viewmodel."""
            edges = self._viewmodel.get_edges()
            
            # Get current edge IDs
            current_ids = {e.edge_id for e in edges}
            existing_ids = set(self._edge_items.keys())
            
            # Remove edges that no longer exist
            for edge_id in existing_ids - current_ids:
                item = self._edge_items.pop(edge_id)
                self.scene.removeItem(item)
            
            # Add new edges (edges don't update state in Stage 1)
            for edge_state in edges:
                if edge_state.edge_id not in self._edge_items:
                    # Get source and target node items
                    source_item = self._node_items.get(edge_state.source_node_id)
                    target_item = self._node_items.get(edge_state.target_node_id)
                    
                    if source_item and target_item:
                        item = EdgeItemView(edge_state, source_item, target_item)
                        self.scene.addItem(item)
                        self._edge_items[edge_state.edge_id] = item
            
            # Update all edge positions (in case nodes moved)
            for edge_item in self._edge_items.values():
                edge_item.update_position()
        
        def wheelEvent(self, event):
            """Handle mouse wheel for zoom."""
            # Get zoom direction
            delta = event.angleDelta().y()
            
            if delta > 0:
                self._viewmodel.zoom_in(1.1)
            else:
                self._viewmodel.zoom_out(1.1)
        
        def get_scene(self) -> QGraphicsScene:
            """Get the graphics scene."""
            return self.scene
        
        def get_view(self) -> QGraphicsView:
            """Get the graphics view."""
            return self.view

else:
    # Stub for when PyQt6 is not available
    class CanvasView:
        def __init__(self, viewmodel, parent=None):
            self._viewmodel = viewmodel
