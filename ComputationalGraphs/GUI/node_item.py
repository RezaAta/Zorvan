"""
GraphicsItem representation of a computational graph node.
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QBrush, QColor, QPen, QFont, QCursor
import colorsys


class NodeItem(QGraphicsEllipseItem):
    """Visual representation of a graph node as a draggable circle."""
    
    def __init__(self, node, x=0, y=0, radius=40):
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        
        self.node = node  # Reference to the actual ComputationalGraph node
        self.radius = radius
        self.input_port = QPointF(0, -radius)  # Top
        self.output_port = QPointF(0, radius)  # Bottom
        self.edges = []  # Connected edge items
        self.hover_edge = False  # Track if hovering over edge
        
        # Visual properties
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Disable caching to avoid trail artifacts
        self.setCacheMode(QGraphicsItem.CacheMode.NoCache)
        
        # Default colors
        self.default_color = QColor(0, 63, 189)  # #003fbd
        self.selected_color = QColor(50, 113, 239)  # Lighter blue for selection
        self.active_color = QColor(100, 180, 255)  # Bright light blue for active nodes
        self.color = None  # Custom color (set by layout/coloring functions)
        self.is_active = False  # Track if node is currently active (for Forward Processing)
        self.setBrush(QBrush(self.default_color))
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        
        # Label
        self.label = QGraphicsTextItem(self.node.name, self)
        self.label.setDefaultTextColor(Qt.GlobalColor.white)
        font = QFont("Arial", 10, QFont.Weight.Bold)
        self.label.setFont(font)
        
        # Center the label
        label_rect = self.label.boundingRect()
        self.label.setPos(-label_rect.width() / 2, -label_rect.height() / 2 - 10)
        
        # Value display
        self.value_label = QGraphicsTextItem("", self)
        self.value_label.setDefaultTextColor(Qt.GlobalColor.white)
        value_font = QFont("Arial", 8)
        self.value_label.setFont(value_font)
        
        self.update_value_display()
        
    def boundingRect(self):
        """Return the bounding rectangle including ports and hover ring."""
        # Extend bounding rect to include ports and hover highlight
        extra = 10  # Extra space for ports and hover ring
        return super().boundingRect().adjusted(-extra, -extra, extra, extra)
    
    def shape(self):
        """Return the shape for collision detection."""
        # Use the default ellipse shape
        return super().shape()
    
    def update_value_display(self):
        """Update the displayed value from the node."""
        # For DataStreamNodes, show the data attribute if value is None
        if hasattr(self.node, 'data') and self.node.value is None and self.node.data:
            # DataStreamNode with data but no value yet
            if isinstance(self.node.data, list) and len(self.node.data) > 0:
                display_text = f"[{len(self.node.data)} samples]"
            else:
                display_text = str(self.node.data)[:20]
        else:
            value = self.node.value
            if value is None:
                display_text = "None"
            elif isinstance(value, (int, float)):
                display_text = f"{value:.2f}" if isinstance(value, float) else str(value)
            elif isinstance(value, list):
                if len(value) <= 3:
                    display_text = str(value)
                else:
                    display_text = f"[{len(value)} items]"
            else:
                display_text = str(value)[:20]
        
        self.value_label.setPlainText(display_text)
        
        # Center the value label
        value_rect = self.value_label.boundingRect()
        self.value_label.setPos(-value_rect.width() / 2, value_rect.height() / 2)
    
    def colorize_by_value(self, min_val=0, max_val=1, min_color=None, max_color=None):
        """Color the node based on its value using a gradient between min_color and max_color.
        
        NOTE: This sets the 'color' attribute, not the brush directly, so it respects
        the active/selected state priority in paint().
        """
        value = self.node.value
        
        # Default colors if not provided
        if min_color is None:
            min_color = QColor(0, 0, 255)  # Blue
        if max_color is None:
            max_color = QColor(255, 0, 0)  # Red
        
        if value is None:
            self.color = QColor(128, 128, 128)  # Gray for None
        # Handle numeric values
        elif isinstance(value, (int, float)):
            # Normalize to 0-1 range
            if max_val != min_val:
                normalized = (value - min_val) / (max_val - min_val)
                normalized = max(0, min(1, normalized))
            else:
                normalized = 0.5
            
            # Interpolate between min_color and max_color
            r = int(min_color.red() + (max_color.red() - min_color.red()) * normalized)
            g = int(min_color.green() + (max_color.green() - min_color.green()) * normalized)
            b = int(min_color.blue() + (max_color.blue() - min_color.blue()) * normalized)
            
            self.color = QColor(r, g, b)
        elif isinstance(value, list):
            # Color based on list length (normalize to 0-10 range)
            normalized = min(len(value) / 10, 1.0)
            
            r = int(min_color.red() + (max_color.red() - min_color.red()) * normalized)
            g = int(min_color.green() + (max_color.green() - min_color.green()) * normalized)
            b = int(min_color.blue() + (max_color.blue() - min_color.blue()) * normalized)
            
            self.color = QColor(r, g, b)
        else:
            # Default color for other types
            self.color = self.default_color
        
        # Trigger repaint to apply the color (respects active state priority)
        self.update()
    
    def add_edge(self, edge):
        """Register an edge connected to this node."""
        self.edges.append(edge)
    
    def remove_edge(self, edge):
        """Unregister an edge."""
        if edge in self.edges:
            self.edges.remove(edge)
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position updates."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Request scene update for old position before moving
            if self.scene():
                self.scene().update()
        
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update all connected edges
            for edge in self.edges:
                edge.update_position()
            
            # Trigger scene update for new position
            if self.scene():
                self.scene().update()
        
        return super().itemChange(change, value)
    
    def get_input_port_scene_pos(self):
        """Get the scene position of the input port."""
        return self.mapToScene(self.input_port)
    
    def get_output_port_scene_pos(self):
        """Get the scene position of the output port."""
        return self.mapToScene(self.output_port)
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection or connection."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking near the edge of the circle for connection
            distance_from_center = (event.pos().x() ** 2 + event.pos().y() ** 2) ** 0.5
            
            # If clicking near the edge (within radius +/- 10 pixels), start connection
            if abs(distance_from_center - self.radius) < 15:
                # Disable movement temporarily
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                
                # Signal to start connection - get the view from the scene
                scene = self.scene()
                if scene and scene.views():
                    view = scene.views()[0]  # Get the first view (GraphCanvas)
                    if hasattr(view, 'start_connection'):
                        view.start_connection(self)
                        event.accept()
                        return
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to open node editor."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get the view and open node editor
            scene = self.scene()
            if scene and scene.views():
                view = scene.views()[0]
                # Get the main window from the view
                main_window = view.window()
                if main_window and hasattr(main_window, 'edit_node'):
                    main_window.edit_node(self)
                    event.accept()
                    return
        
        super().mouseDoubleClickEvent(event)
    
    def paint(self, painter, option, widget):
        """Custom paint to show selection state and active nodes."""
        # Priority: Active > Selected > Custom > Default
        if self.is_active:
            # Active nodes get the brightest color (thinking brain effect)
            self.setBrush(QBrush(self.active_color))
        elif self.isSelected():
            self.setBrush(QBrush(self.selected_color))
        elif self.color is not None:
            # Use custom color if set (from layout/coloring)
            self.setBrush(QBrush(self.color))
        else:
            # Restore default color when deselected
            self.setBrush(QBrush(self.default_color))
        
        super().paint(painter, option, widget)
        
        # If hovering over edge, draw a highlighted ring
        if self.hover_edge:
            painter.setPen(QPen(QColor(255, 200, 0), 3))  # Orange highlight
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
    
    def set_active(self, active):
        """Set whether this node is currently active (for Forward Processing)."""
        self.is_active = active
        self.update()  # Trigger repaint
    
    def hoverMoveEvent(self, event):
        """Handle hover to show connection cursor."""
        from PyQt6.QtGui import QCursor
        
        # Check if hovering near the edge
        distance_from_center = (event.pos().x() ** 2 + event.pos().y() ** 2) ** 0.5
        
        # If hovering near the edge, show crosshair cursor
        if abs(distance_from_center - self.radius) < 15:
            self.hover_edge = True
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.hover_edge = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        
        self.update()  # Trigger repaint
        super().hoverMoveEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Reset cursor when leaving node."""
        self.hover_edge = False
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.update()
        super().hoverLeaveEvent(event)
