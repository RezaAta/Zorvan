"""
GraphicsItem representation of edges connecting nodes.
"""

from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QPainterPath, QColor, QBrush, QPolygonF
import math


class EdgeItem(QGraphicsPathItem):
    """Visual representation of an edge connecting two nodes with dynamic arrow."""
    
    def __init__(self, source_node, target_node):
        super().__init__()
        
        self.source_node = source_node  # NodeItem
        self.target_node = target_node  # NodeItem
        
        # Visual properties
        self.setPen(QPen(QColor(80, 80, 80), 2))
        self.setZValue(-1)  # Draw edges behind nodes
        
        # Arrow properties
        self.arrow_size = 12
        
        # Register with nodes
        self.source_node.add_edge(self)
        self.target_node.add_edge(self)
        
        self.update_position()
    
    def update_position(self):
        """Recalculate the path based on node positions with dynamic connection points."""
        # Get center positions of both nodes
        source_center = self.source_node.scenePos()
        target_center = self.target_node.scenePos()
        
        # Calculate the direction vector
        dx = target_center.x() - source_center.x()
        dy = target_center.y() - source_center.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return  # Nodes are at same position
        
        # Normalize direction
        dx_norm = dx / distance
        dy_norm = dy / distance
        
        # Calculate start point (on source node edge)
        source_radius = self.source_node.radius
        start = QPointF(
            source_center.x() + dx_norm * source_radius,
            source_center.y() + dy_norm * source_radius
        )
        
        # Calculate end point (on target node edge, leaving space for arrow)
        target_radius = self.target_node.radius
        end = QPointF(
            target_center.x() - dx_norm * (target_radius + self.arrow_size),
            target_center.y() - dy_norm * (target_radius + self.arrow_size)
        )
        
        # Create a smooth curve
        path = QPainterPath()
        path.moveTo(start)
        
        # Use bezier curve for smooth connection
        # Calculate control points based on distance and direction
        ctrl_offset = distance * 0.25
        
        # Perpendicular offset for curved path
        perp_x = -dy_norm * ctrl_offset * 0.3
        perp_y = dx_norm * ctrl_offset * 0.3
        
        ctrl1 = QPointF(
            start.x() + dx_norm * ctrl_offset + perp_x,
            start.y() + dy_norm * ctrl_offset + perp_y
        )
        ctrl2 = QPointF(
            end.x() - dx_norm * ctrl_offset + perp_x,
            end.y() - dy_norm * ctrl_offset + perp_y
        )
        
        path.cubicTo(ctrl1, ctrl2, end)
        
        self.setPath(path)
    
    def paint(self, painter, option, widget):
        """Paint the edge with an arrow head."""
        # Draw the path (the line)
        super().paint(painter, option, widget)
        
        # Calculate arrow head position and angle
        source_center = self.source_node.scenePos()
        target_center = self.target_node.scenePos()
        
        dx = target_center.x() - source_center.x()
        dy = target_center.y() - source_center.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return
        
        # Normalize
        dx_norm = dx / distance
        dy_norm = dy / distance
        
        # Arrow head position (at the target node edge)
        target_radius = self.target_node.radius
        arrow_pos = QPointF(
            target_center.x() - dx_norm * target_radius,
            target_center.y() - dy_norm * target_radius
        )
        
        # Calculate arrow angle
        angle = math.atan2(dy, dx)
        
        # Create arrow head points
        arrow_p1 = arrow_pos
        arrow_p2 = QPointF(
            arrow_pos.x() - self.arrow_size * math.cos(angle - math.pi / 6),
            arrow_pos.y() - self.arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p3 = QPointF(
            arrow_pos.x() - self.arrow_size * math.cos(angle + math.pi / 6),
            arrow_pos.y() - self.arrow_size * math.sin(angle + math.pi / 6)
        )
        
        # Draw filled arrow head
        arrow_head = QPolygonF([arrow_p1, arrow_p2, arrow_p3])
        painter.setBrush(QBrush(self.pen().color()))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow_head)
    
    def remove(self):
        """Remove this edge from the scene and unregister from nodes."""
        self.source_node.remove_edge(self)
        self.target_node.remove_edge(self)
        
        if self.scene():
            self.scene().removeItem(self)
