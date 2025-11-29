"""
GraphicsItem representation of a computational graph node.
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem, QStyleOptionGraphicsItem, QStyle
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QBrush, QColor, QPen, QFont, QCursor
from PyQt6.QtWidgets import QMenu
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
        self.connection_highlight = False  # Highlight for multi-connection
        
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
        # Populate with initial value
        self.update_value_display()

    def set_label_text(self, text: str):
        """Set the node label text and re-center it above the node.

        This method should be used whenever the label text changes (e.g., when
        renaming a node) to ensure the text remains centered.
        """
        try:
            self.label.setPlainText(text)
            # Reapply font to ensure layout is updated consistently
            # (some platforms may not update layout immediately otherwise)
            font = self.label.font()
            self.label.setFont(font)
            label_rect = self.label.boundingRect()
            self.label.setPos(-label_rect.width() / 2, -label_rect.height() / 2 - 10)
        except Exception:
            # Fall back to plain set if anything goes wrong
            try:
                self.label.setPlainText(text)
            except Exception:
                pass
        
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
        # Ensure value_label exists (defensive: some NodeItem instances saved/restored
        # or partially initialized may not have the attribute). Create if missing.
        if not hasattr(self, 'value_label') or self.value_label is None:
            try:
                self.value_label = QGraphicsTextItem("", self)
                self.value_label.setDefaultTextColor(Qt.GlobalColor.white)
                value_font = QFont("Arial", 8)
                self.value_label.setFont(value_font)
            except Exception:
                # If creating the value label fails, skip updating the label
                return
        # For DataStreamNodes, show the data attribute if value is None
        if hasattr(self.node, 'data') and self.node.value is None and self.node.data:
            # DataStreamNode with data but no value yet
            if isinstance(self.node.data, list) and len(self.node.data) > 0:
                display_text = f"[{len(self.node.data)} samples]"
            else:
                display_text = str(self.node.data)[:20]
        else:
            # For BufferNodes, show the delayed (oldest) output.
            # Avoid falling through to the generic formatting logic that expects `value` to be defined,
            # which causes an unbound-local error on the buffered branch.
            if hasattr(self.node, 'buffer'):
                val = self.node.value
                def fmt(x):
                    if x is None:
                        return "None"
                    elif isinstance(x, float):
                        return f"{x:.2f}"
                    elif isinstance(x, int):
                        return str(x)
                    else:
                        return str(x)

                display_text = f"{fmt(val)}"
                self.value_label.setPlainText(display_text)
                # Center the value label
                value_rect = self.value_label.boundingRect()
                self.value_label.setPos(-value_rect.width() / 2, value_rect.height() / 2)
                return
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
            # Live snapping while dragging
            try:
                canvas = getattr(self, 'canvas', None)
                # Fallback: attempt to get the view (GraphCanvas) assigned to the scene
                if canvas is None and self.scene() and self.scene().views():
                    try:
                        view = self.scene().views()[0]
                        # If the view is the GraphCanvas instance, use it
                        if hasattr(view, 'snap_to_grid'):
                            canvas = view
                    except Exception:
                        pass
                if canvas and getattr(canvas, 'snap_to_grid', False) and getattr(canvas, 'snap_while_dragging', False):
                    # `value` is a QPointF with the proposed new position
                    from PyQt6.QtCore import QPointF
                    p = value
                    g = getattr(canvas, 'grid_size', 0)
                    if g and g > 0:
                        step = getattr(canvas, 'snap_step', 1)
                        unit = g * (int(step) if step else 1)
                        sx = round(p.x() / unit) * unit
                        sy = round(p.y() / unit) * unit
                        return QPointF(sx, sy)
            except Exception:
                pass
        
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update all connected edges
            for edge in self.edges:
                edge.update_position()
            
            # Trigger scene update for new position
            if self.scene():
                self.scene().update()
            # Snap on release if enabled
            try:
                canvas = getattr(self, 'canvas', None)
                # Fallback: attempt to get the view (GraphCanvas) assigned to the scene
                if canvas is None and self.scene() and self.scene().views():
                    try:
                        view = self.scene().views()[0]
                        if hasattr(view, 'snap_to_grid'):
                            canvas = view
                    except Exception:
                        pass
                if canvas and getattr(canvas, 'snap_to_grid', False) and not getattr(canvas, 'snap_while_dragging', False):
                    # Snap to nearest unit after move completed
                    g = getattr(canvas, 'grid_size', 0)
                    if g and g > 0:
                        step = getattr(canvas, 'snap_step', 1)
                        unit = g * (int(step) if step else 1)
                        p = self.pos()
                        sx = round(p.x() / unit) * unit
                        sy = round(p.y() / unit) * unit
                        # Avoid infinite loop; only set if different
                        from PyQt6.QtCore import QPointF
                        if abs(sx - p.x()) > 0.0001 or abs(sy - p.y()) > 0.0001:
                            self.setPos(QPointF(sx, sy))
                            # Update edges after snapping
                            for edge in self.edges:
                                edge.update_position()
            except Exception:
                pass
        
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

    def contextMenuEvent(self, event):
        try:
            menu = QMenu()
            # View predecessors menu item
            view_pred_action = menu.addAction("View Predecessors")
            action = menu.exec(event.screenPos())
            if action == view_pred_action:
                try:
                    canvas = getattr(self, 'canvas', None)
                    if canvas and hasattr(canvas, 'graph') and canvas.graph is not None:
                        from .predecessors_dialog import PredecessorsDialog
                        dlg = PredecessorsDialog(self, canvas, parent=self.scene().views()[0].window())
                        dlg.exec()
                except Exception:
                    pass
        except Exception:
            pass
    
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
        
        # Call base paint but avoid drawing the default selected bounding box
        try:
            opt = QStyleOptionGraphicsItem(option)
            # Clear the Selected state flag so Qt won't draw the dotted bbox
            try:
                opt.state &= ~QStyle.StateFlag.State_Selected
            except Exception:
                # Fallback for some PyQt6 builds
                opt.state &= ~QStyle.State.State_Selected
            super().paint(painter, opt, widget)
        except Exception:
            # If anything goes wrong, fall back to default behavior
            super().paint(painter, option, widget)
        
        # If hovering over edge, draw a highlighted ring
        if self.hover_edge:
            painter.setPen(QPen(QColor(255, 200, 0), 3))  # Orange highlight
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        # Connection highlight applies to all selected nodes while connecting
        elif self.connection_highlight:
            painter.setPen(QPen(QColor(255, 215, 0), 3))  # Yellow-ish ring
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
    
    def set_active(self, active):
        """Set whether this node is currently active (for Forward Processing)."""
        self.is_active = active
        self.update()  # Trigger repaint

    def set_connection_highlight(self, val: bool):
        """Highlight this node as part of a multi-connection preview."""
        self.connection_highlight = bool(val)
        self.update()
    
    def hoverMoveEvent(self, event):
        """Handle hover to show connection cursor."""
        from PyQt6.QtGui import QCursor
        
        # Check if hovering near the edge
        distance_from_center = (event.pos().x() ** 2 + event.pos().y() ** 2) ** 0.5
        
        # If hovering near the edge, show crosshair cursor
        if abs(distance_from_center - self.radius) < 15:
            self.hover_edge = True
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            # If this node is selected, notify the view to highlight all selected nodes
            if self.isSelected():
                scene = self.scene()
                if scene and scene.views():
                    view = scene.views()[0]
                    if hasattr(view, 'highlight_selected_nodes_for_connection'):
                        view.highlight_selected_nodes_for_connection(True)
        else:
            self.hover_edge = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            # Remove selected nodes highlight when not hovering
            if self.isSelected():
                scene = self.scene()
                if scene and scene.views():
                    view = scene.views()[0]
                    if hasattr(view, 'highlight_selected_nodes_for_connection') and not getattr(view, 'connection_mode', False):
                        view.highlight_selected_nodes_for_connection(False)
        
        self.update()  # Trigger repaint
        super().hoverMoveEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Reset cursor when leaving node."""
        self.hover_edge = False
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        # Remove selected nodes highlight when leaving this node
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'highlight_selected_nodes_for_connection') and not getattr(view, 'connection_mode', False):
                view.highlight_selected_nodes_for_connection(False)
        self.update()
        super().hoverLeaveEvent(event)
