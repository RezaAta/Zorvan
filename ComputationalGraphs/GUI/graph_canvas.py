"""
QGraphicsView-based canvas for displaying and editing the computational graph.
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor
from .node_item import NodeItem
from .edge_item import EdgeItem


class GraphCanvas(QGraphicsView):
    """Interactive canvas for node graph editing."""
    
    node_selected = pyqtSignal(object)  # Emits the selected node
    edge_created = pyqtSignal(object, object)  # Emits (source_node, target_node)
    edge_removed = pyqtSignal(object, object)  # Emits (source_node, target_node) when an edge is removed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Scene settings
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        self.scene.setBackgroundBrush(QColor(35, 35, 35))  # Dark background
        
        # View settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setBackgroundBrush(QColor(35, 35, 35))  # Match scene background
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Connection state
        self.connection_mode = False
        self.connection_start_nodes = []  # List[NodeItem] when multi-connecting
        self.temp_connection_lines = []  # List of QGraphicsLineItem for preview
        
        # Panning state
        self.panning = False
        self.pan_start_pos = None
        
        # Grid / snap settings
        self.node_diameter = 80  # Default assumed diameter (2 * radius 40)
        self.grid_mode = '4x4'  # '1x1' or '4x4'
        self.grid_size = int(self.node_diameter / 4)  # 20px by default
        self.grid_major_every = 4  # draw a major line every 4 cells (node size)
        self.grid_minor_color = QColor(45, 45, 45)
        self.grid_major_color = QColor(70, 70, 70)
        self.show_grid = False
        self.snap_to_grid = True
        self.snap_while_dragging = True  # default: snap while dragging so users see snap live
        self.snap_step = 4  # Snap in units of grid cells (4 -> node sized step)
        
        # Node tracking
        self.node_items = {}  # Maps node objects to NodeItem widgets
        self.edge_items = []
        # Internal clipboard for copy/paste
        self._clipboard = None
        
    def add_node_item(self, node, x=0, y=0):
        """Add a visual representation of a node to the canvas."""
        # snap initial position if enabled
        try:
            if getattr(self, 'snap_to_grid', False) and getattr(self, 'grid_size', 0) > 0:
                x, y = self.snap_point(x, y, step=self.snap_step)
        except Exception:
            pass

        node_item = NodeItem(node, x, y)
        # Allow NodeItem to reference the canvas for snapping live
        try:
            node_item.canvas = self
        except Exception:
            pass
        self.scene.addItem(node_item)
        self.node_items[node] = node_item
        # Ensure value_label exists for older or partially-initialized node items
        try:
            if not hasattr(node_item, 'value_label') or node_item.value_label is None:
                from PyQt6.QtWidgets import QGraphicsTextItem
                node_item.value_label = QGraphicsTextItem("", node_item)
                node_item.value_label.setDefaultTextColor(Qt.GlobalColor.white)
                from PyQt6.QtGui import QFont
                node_item.value_label.setFont(QFont("Arial", 8))
        except Exception:
            # If creation fails, don't block adding the node - leave as-is and skip value display
            pass
        # Populate the initial value display
        try:
            node_item.update_value_display()
        except Exception:
            pass
        return node_item

    def set_show_grid(self, enabled: bool):
        """Enable or disable drawing of the grid background."""
        self.show_grid = bool(enabled)
        try:
            self.viewport().update()
        except Exception:
            pass

    def set_snap_to_grid(self, enabled: bool):
        """Enable or disable snapping nodes to the grid."""
        self.snap_to_grid = bool(enabled)

    def set_snap_while_dragging(self, enabled: bool):
        """Enable or disable snapping while dragging (live) vs on release."""
        self.snap_while_dragging = bool(enabled)

    def set_grid_mode(self, mode: str):
        """Set grid mode: '1x1' for node=1 cell, '4x4' for node=4 cells. Mode affects grid_size."""
        try:
            node_diam = getattr(self, 'node_diameter', 80)
            if mode == '1x1':
                self.grid_size = node_diam
                self.snap_step = 1
            else:
                # default to 4x4 grid
                self.grid_size = max(1, int(node_diam / 4))
                self.snap_step = 4
            self.grid_mode = mode
            try:
                self.viewport().update()
            except Exception:
                pass
        except Exception:
            pass

    def snap_point(self, x: float, y: float, step: int = None):
        """Return the snapped position according to grid settings.

        If step is None use self.snap_step.
        """
        if not getattr(self, 'snap_to_grid', False):
            return x, y
        if getattr(self, 'grid_size', 0) <= 0:
            return x, y
        try:
            s = int(step or getattr(self, 'snap_step', 1))
            unit = self.grid_size * s
            sx = round(x / unit) * unit
            sy = round(y / unit) * unit
            return sx, sy
        except Exception:
            return x, y

    def drawBackground(self, painter, rect):
        """Draw a subtle grid on the background when enabled.

        Draw only in the visible rect for performance.
        """
        # Default dark background already set; draw grid lines on top
        super().drawBackground(painter, rect)
        if not getattr(self, 'show_grid', False):
            return
        # grid size in pixels
        g = getattr(self, 'grid_size', 20)
        if g <= 0:
            return

        from PyQt6.QtGui import QPen, QPainter
        import math
        left = int(math.floor(rect.left() / g) * g)
        right = int(math.ceil(rect.right() / g) * g)
        top = int(math.floor(rect.top() / g) * g)
        bottom = int(math.ceil(rect.bottom() / g) * g)

        minor_pen = QPen(self.grid_minor_color, 1)
        major_pen = QPen(self.grid_major_color, 1)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        x = left
        while x <= right:
            pen = major_pen if ((x // g) % self.grid_major_every == 0) else minor_pen
            painter.setPen(pen)
            painter.drawLine(x, top, x, bottom)
            x += g

        y = top
        while y <= bottom:
            pen = major_pen if ((y // g) % self.grid_major_every == 0) else minor_pen
            painter.setPen(pen)
            painter.drawLine(left, y, right, y)
            y += g
    
    def add_edge_item(self, source_node, target_node):
        """Add a visual edge between two nodes."""
        source_item = self.node_items.get(source_node)
        target_item = self.node_items.get(target_node)
        
        if source_item and target_item:
            edge_item = EdgeItem(source_item, target_item)
            self.scene.addItem(edge_item)
            self.edge_items.append(edge_item)
            self.edge_created.emit(source_node, target_node)
            # If canvas holds a graph reference, update the graph connectivity
            try:
                if hasattr(self, 'graph') and getattr(self, 'graph') is not None:
                    # Only connect if the nodes belong to the authoritative graph
                    try:
                        if target_node in getattr(self.graph, 'nodes', []) and source_node in getattr(self.graph, 'nodes', []):
                            self.graph.ConnectPreNode(target_node, source_node)
                    except Exception:
                        # If the connection fails, continue without blocking UI
                        pass
            except Exception:
                pass
            return edge_item
        
        return None
    
    def remove_selected_items(self):
        """Remove selected nodes and edges."""
        selected = self.scene.selectedItems()
        
        for item in selected:
            if isinstance(item, NodeItem):
                # Remove connected edges first
                for edge in item.edges[:]:
                    # Disconnect underlying Graph link if present
                    try:
                        # emit edge_removed for listeners before we physically remove it
                        src = edge.source_node.node
                        tgt = edge.target_node.node
                        try:
                            self.edge_removed.emit(src, tgt)
                        except Exception:
                            pass
                        if hasattr(self, 'graph') and getattr(self, 'graph') is not None:
                            # Only disconnect if these nodes are in the authoritative graph
                            try:
                                if tgt in getattr(self.graph, 'nodes', []) and src in getattr(self.graph, 'nodes', []):
                                    self.graph.DisconnectPreNode(tgt, src)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    edge.remove()
                    if edge in self.edge_items:
                        self.edge_items.remove(edge)
                
                # Remove node item
                if item.node in self.node_items:
                    del self.node_items[item.node]
                
                self.scene.removeItem(item)
            
            elif isinstance(item, EdgeItem):
                # Update the computational graph if available
                try:
                    if hasattr(self, 'graph') and getattr(self, 'graph') is not None:
                        src = item.source_node.node
                        tgt = item.target_node.node
                        try:
                            self.edge_removed.emit(src, tgt)
                        except Exception:
                            pass
                        try:
                            if tgt in getattr(self.graph, 'nodes', []) and src in getattr(self.graph, 'nodes', []):
                                self.graph.DisconnectPreNode(tgt, src)
                        except Exception:
                            pass
                except Exception:
                    pass
                item.remove()
                if item in self.edge_items:
                    self.edge_items.remove(item)
    
    def start_connection(self, node_item):
        """Start creating a connection from a node."""
        # If multiple nodes selected and node_item is among them, connect all selected nodes
        selected = [item for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        if len(selected) > 1 and node_item in selected:
            self.connection_start_nodes = selected
        else:
            self.connection_start_nodes = [node_item]

        # Turn on connection mode and disable movement on start nodes
        self.connection_mode = True
        for n in self.connection_start_nodes:
            n.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            # Also set the connection highlight
            n.set_connection_highlight(True)

        # Disable rubberband selection and enable drawing
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
    
    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel."""
        zoom_factor = 1.15
        
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom out
            self.scale(1 / zoom_factor, 1 / zoom_factor)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # Fit view
        if event.key() == Qt.Key.Key_F:
            self.fit_all_nodes_in_view()
        # Delete selected nodes/edges
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.remove_selected_items()
        # Copy / Paste / Cut (Ctrl+C / Ctrl+V / Ctrl+X)
        elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.copy_selected()
        elif event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.paste_clipboard()
        elif event.key() == Qt.Key.Key_X and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.cut_selected()
        else:
            super().keyPressEvent(event)

    def copy_selected(self):
        """Copy currently selected node items (and internal edges between them) to internal clipboard."""
        selected = [item for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        if not selected:
            return

        # Build node data list
        nodes_data = []
        node_to_index = {}
        for idx, item in enumerate(selected):
            node = item.node
            node_to_index[node] = idx
            # Collect simple attributes (primitives and lists/dicts)
            attrs = {}
            for attr in ('value', 'data', 'size'):
                if hasattr(node, attr):
                    val = getattr(node, attr)
                    # shallow copy for lists/dicts
                    try:
                        if isinstance(val, (list, dict)):
                            import copy as _copy
                            attrs[attr] = _copy.copy(val)
                        else:
                            attrs[attr] = val
                    except Exception:
                        pass

            nodes_data.append({
                'class': node.__class__,
                'name': node.name if hasattr(node, 'name') else None,
                'attrs': attrs,
                'pos': (item.pos().x(), item.pos().y())
            })

        # Collect internal edges (between selected nodes)
        edges = []
        for edge in list(self.edge_items):
            s = edge.source_node.node
            t = edge.target_node.node
            if s in node_to_index and t in node_to_index:
                edges.append((node_to_index[s], node_to_index[t]))

        self._clipboard = {
            'nodes': nodes_data,
            'edges': edges
        }

    def paste_clipboard(self):
        """Paste nodes from internal clipboard into the scene, centered in view."""
        if not self._clipboard:
            return

        data = self._clipboard
        nodes_data = data.get('nodes', [])
        edges = data.get('edges', [])

        # Compute average original position
        if not nodes_data:
            return

        avg_x = sum(p['pos'][0] for p in nodes_data) / len(nodes_data)
        avg_y = sum(p['pos'][1] for p in nodes_data) / len(nodes_data)

        # Paste center at current view center
        center_point = self.mapToScene(self.viewport().rect().center())
        dx = center_point.x() - avg_x
        dy = center_point.y() - avg_y

        new_items = []
        for node_info in nodes_data:
            cls = node_info['class']
            orig_name = node_info.get('name') or 'Node'
            # Create a new name to avoid collisions
            new_name = f"{orig_name}_copy"
            try:
                # Try to instantiate with name param
                new_node = cls(name=new_name)
            except Exception:
                try:
                    # Fallback: instantiate without args
                    new_node = cls()
                    if hasattr(new_node, 'name'):
                        new_node.name = new_name
                except Exception:
                    # Unable to create node of this type; skip
                    continue

            # Restore simple attributes
            for k, v in node_info.get('attrs', {}).items():
                try:
                    setattr(new_node, k, v)
                except Exception:
                    pass

            # Position
            ox, oy = node_info.get('pos', (0, 0))
            new_item = self.add_node_item(new_node, ox + dx + 20, oy + dy + 20)
            new_items.append(new_item)

        # Recreate edges between pasted items
        for s_idx, t_idx in edges:
            if s_idx < len(new_items) and t_idx < len(new_items):
                s_node = new_items[s_idx].node
                t_node = new_items[t_idx].node
                self.add_edge_item(s_node, t_node)

        # Select pasted items
        for item in new_items:
            item.setSelected(True)

    def cut_selected(self):
        """Cut selected nodes (copy then delete)."""
        self.copy_selected()
        self.remove_selected_items()
    
    def fit_all_nodes_in_view(self):
        """Center and zoom to fit all nodes in the viewport."""
        if not self.node_items:
            return
        
        # Get bounding rect of all nodes
        all_rects = []
        for node_item in self.node_items.values():
            all_rects.append(node_item.sceneBoundingRect())
        
        if not all_rects:
            return
        
        # Calculate union of all bounding rects
        # QRectF is not required explicitly; united_rect created by union operations is used directly
        united_rect = all_rects[0]
        for rect in all_rects[1:]:
            united_rect = united_rect.united(rect)
        
        # Add some padding (10% on each side)
        padding = max(united_rect.width(), united_rect.height()) * 0.1
        united_rect.adjust(-padding, -padding, padding, padding)
        
        # Fit the rect in view
        self.fitInView(united_rect, Qt.AspectRatioMode.KeepAspectRatio)
        
        # Limit maximum zoom to avoid making nodes too large
        current_transform = self.transform()
        scale_factor = current_transform.m11()  # Get x-axis scale
        if scale_factor > 2.0:
            # If zoomed in too much, scale back to 2.0x
            self.resetTransform()
            self.scale(2.0, 2.0)
            self.centerOn(united_rect.center())
    
    def mousePressEvent(self, event):
        """Handle mouse press for panning with middle button."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Start panning
            self.panning = True
            self.pan_start_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for connection drawing and panning."""
        if self.panning and self.pan_start_pos:
            # Pan the view
            delta = event.position() - self.pan_start_pos
            self.pan_start_pos = event.position()
            
            # Move the scrollbars
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
        elif self.connection_mode and self.connection_start_nodes:
            # Draw temporary line
            from PyQt6.QtWidgets import QGraphicsLineItem
            if not self.temp_connection_lines:
                # Create a preview line for each start node
                for n in self.connection_start_nodes:
                    line = QGraphicsLineItem()
                    line.setPen(QPen(QColor(100, 100, 100), 2, Qt.PenStyle.DashLine))
                    self.scene.addItem(line)
                    self.temp_connection_lines.append(line)
            
            # Update lines for each start node
            end_pos = self.mapToScene(event.position().toPoint())
            for i, n in enumerate(self.connection_start_nodes):
                start_pos = n.scenePos()
                self.temp_connection_lines[i].setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for connection completion and panning."""
        if event.button() == Qt.MouseButton.MiddleButton and self.panning:
            # Stop panning
            self.panning = False
            self.pan_start_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        elif self.connection_mode and self.connection_start_nodes:
            # Check if released over another node
            pos = self.mapToScene(event.position().toPoint())
            items = self.scene.items(pos)
            
            target_node = None
            for item in items:
                if isinstance(item, NodeItem) and item not in self.connection_start_nodes:
                    # Accept connection if released anywhere on the target node
                    target_node = item
                    break
            
            if target_node:
                # Create edges from all start nodes to this target
                for start in self.connection_start_nodes:
                    if start.node != target_node.node:
                        self.add_edge_item(start.node, target_node.node)
            
            # Clean up
            if self.temp_connection_lines:
                for line in self.temp_connection_lines:
                    try:
                        self.scene.removeItem(line)
                    except Exception:
                        pass
                self.temp_connection_lines = []
            
            # Re-enable movement on the source node(s) and remove their connection highlight
            for n in self.connection_start_nodes:
                n.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
                n.set_connection_highlight(False)
            
            self.connection_mode = False
            self.connection_start_nodes = []
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        super().mouseReleaseEvent(event)
    
    def dragEnterEvent(self, event):
        """Accept drag events from the palette."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Accept drag move events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event to create new node."""
        if event.mimeData().hasText():
            node_type = event.mimeData().text()
            drop_pos = self.mapToScene(event.position().toPoint())
            
            # Import all node types
            from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
            from ComputationalGraphs.Nodes.DynamicDataStreamNode import DynamicDataStreamNode
            from ComputationalGraphs.Nodes.BufferNode import BufferNode
            from ComputationalGraphs.Nodes.SequencerNode import SequencerNode
            from ComputationalGraphs.Nodes.ListNode import ListNode
            from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
            from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
            from ComputationalGraphs.Nodes.SubtractionNode import SubtractionNode
            from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
            from ComputationalGraphs.Nodes.DivisionNode import DivisionNode
            from ComputationalGraphs.Nodes.MaxNode import MaxNode
            from ComputationalGraphs.Nodes.MinNode import MinNode
            from ComputationalGraphs.Nodes.MeanSquaredErrorNode import MeanSquaredErrorNode
            from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
            from ComputationalGraphs.Nodes.SigmoidDerivativeNode import SigmoidDerivativeNode
            from ComputationalGraphs.Nodes.ReLUNode import ReLUNode
            from ComputationalGraphs.Nodes.ReLUDerivativeNode import ReLUDerivativeNode
            from ComputationalGraphs.Nodes.LinearNode import LinearNode
            from ComputationalGraphs.Nodes.TanhNode import TanhNode
            from ComputationalGraphs.Nodes.TanhDerivativeNode import TanhDerivativeNode
            from ComputationalGraphs.Nodes.GaussianNode import GaussianNode
            from ComputationalGraphs.Nodes.PiecewiseLinearNode import PiecewiseLinearNode
            from ComputationalGraphs.Nodes.TournamentSelectionNode import TournamentSelectionNode
            from ComputationalGraphs.Nodes.BulkTournamentNode import BulkTournamentNode
            from ComputationalGraphs.Nodes.CrossoverNode import CrossoverNode
            from ComputationalGraphs.Nodes.SingleCrossoverNode import SingleCrossoverNode
            from ComputationalGraphs.Nodes.MutationNode import MutaionNode
            from ComputationalGraphs.Nodes.DeJongSphereNode import DeJongSphereNode
            from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
            from ComputationalGraphs.Nodes.ExtractListElement import ExtractListElement
            
            node = None
            node_id = len(self.node_items)
            
            # Data nodes
            if node_type == "DataStreamNode":
                node = DataStreamNode(name=f"Data_{node_id}", data=[1, 2, 3, 4, 5])
            elif node_type == "DynamicDataStreamNode":
                node = DynamicDataStreamNode(name=f"DynData_{node_id}")
            elif node_type == "BufferNode":
                node = BufferNode(name=f"Buffer_{node_id}", size=3)
            elif node_type == "MovingAverageNode":
                from ComputationalGraphs.Nodes.MovingAverageNode import MovingAverageNode
                node = MovingAverageNode(name=f"MovAvg_{node_id}", size=10, mode='continuous')
            elif node_type == "SequencerNode":
                node = SequencerNode(name=f"Seq_{node_id}")
            elif node_type == "ListNode":
                node = ListNode(name=f"List_{node_id}")
            elif node_type == "ExtractListElement":
                # Default to extracting index 0; user can edit properties later
                node = ExtractListElement(name=f"ExtractList_{node_id}", index=0)
            elif node_type == "ContainerNode":
                node = ContainerNode(name=f"Container_{node_id}")
            
            # Arithmetic nodes
            elif node_type == "AdditionNode":
                node = AdditionNode(name=f"Add_{node_id}")
            elif node_type == "SubtractionNode":
                node = SubtractionNode(name=f"Sub_{node_id}")
            elif node_type == "MultiplicationNode":
                node = MultiplicationNode(name=f"Mul_{node_id}")
            elif node_type == "DivisionNode":
                node = DivisionNode(name=f"Div_{node_id}")
            
            # Statistical nodes
            elif node_type == "MaxNode":
                node = MaxNode(name=f"Max_{node_id}")
            elif node_type == "MinNode":
                node = MinNode(name=f"Min_{node_id}")
            elif node_type == "MeanSquaredErrorNode":
                node = MeanSquaredErrorNode(name=f"MSE_{node_id}")
            
            # Activation functions
            elif node_type == "SigmoidNode":
                node = SigmoidNode(name=f"Sigmoid_{node_id}")
            elif node_type == "SigmoidDerivativeNode":
                node = SigmoidDerivativeNode(name=f"Sigmoid'_{node_id}")
            elif node_type == "ReLUNode":
                node = ReLUNode(name=f"ReLU_{node_id}")
            elif node_type == "ReLUDerivativeNode":
                node = ReLUDerivativeNode(name=f"ReLU'_{node_id}")
            elif node_type == "LinearNode":
                node = LinearNode(name=f"Linear_{node_id}")
            elif node_type == "TanhNode":
                node = TanhNode(name=f"Tanh_{node_id}")
            elif node_type == "TanhDerivativeNode":
                node = TanhDerivativeNode(name=f"Tanh'_{node_id}")
            elif node_type == "GaussianNode":
                node = GaussianNode(name=f"Gauss_{node_id}")
            elif node_type == "PiecewiseLinearNode":
                node = PiecewiseLinearNode(name=f"Piecewise_{node_id}")
            
            # Evolutionary algorithm nodes
            elif node_type == "TournamentSelectionNode":
                node = TournamentSelectionNode(name=f"Tournament_{node_id}")
            elif node_type == "BulkTournamentNode":
                node = BulkTournamentNode(name=f"BulkTour_{node_id}")
            elif node_type == "CrossoverNode":
                node = CrossoverNode(name=f"Crossover_{node_id}")
            elif node_type == "SingleCrossoverNode":
                node = SingleCrossoverNode(name=f"SingleXO_{node_id}")
            elif node_type == "MutationNode":
                node = MutaionNode(name=f"Mutation_{node_id}")
            elif node_type == "DeJongSphereNode":
                node = DeJongSphereNode(name=f"DeJong_{node_id}")
            
            # Utility nodes
            elif node_type == "DisplayNode":
                node = DisplayNode(name=f"Display_{node_id}")
            
            if node:
                self.add_node_item(node, drop_pos.x(), drop_pos.y())
                event.acceptProposedAction()
    
    def update_node_visuals(self, colorize=False, min_val=0, max_val=1, min_color=None, max_color=None):
        """Update all node visuals (values and optionally colors)."""
        for node_item in self.node_items.values():
            node_item.update_value_display()
            if colorize:
                node_item.colorize_by_value(min_val, max_val, min_color, max_color)

    def highlight_selected_nodes_for_connection(self, on: bool):
        """Highlight all currently selected nodes for connection preview."""
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        for item in selected_items:
            item.set_connection_highlight(on)
    
    def highlight_active_nodes(self, active_nodes):
        """Highlight active nodes during Forward Processing execution.
        
        Args:
            active_nodes: List of Node objects that are currently active
        """
        active_node_set = set(active_nodes)
        
        for node, node_item in self.node_items.items():
            is_active = node in active_node_set
            node_item.set_active(is_active)
    
    def apply_layout(self, layout_type="spring"):
        """Apply an automatic layout algorithm to nodes with better spacing."""
        if not self.node_items:
            return
        
        try:
            import networkx as nx
            
            # Build networkx graph
            G = nx.DiGraph()
            for node in self.node_items.keys():
                G.add_node(node)
            
            for edge_item in self.edge_items:
                G.add_edge(edge_item.source_node.node, edge_item.target_node.node)
            
            # Calculate appropriate scale based on number of nodes
            num_nodes = len(G.nodes())
            base_scale = 300  # Optimal base scale
            scale = base_scale * max(1.0, num_nodes / 15)  # Scale up for larger graphs
            
            # Compute layout with better parameters
            if layout_type == "spring":
                # Spring layout with better spacing
                pos = nx.spring_layout(
                    G, 
                    k=2.0/num_nodes**0.5,  # Optimal distance between nodes
                    iterations=100,  # More iterations for better convergence
                    scale=scale,
                    seed=42  # Reproducible layout
                )
            elif layout_type == "ann":
                # ANN-specific layout: Left-to-right with layer-based positioning
                pos = self._compute_ann_layout(G, scale)
            elif layout_type == "good":
                # The Good Layout: cellular grid MLP layout (deterministic)
                pos = self._compute_good_layout(G, scale)
            elif layout_type == "hierarchical":
                # Try to use shell/layered layout for hierarchical structure
                try:
                    # Try to detect layers using topological sort
                    if nx.is_directed_acyclic_graph(G):
                        # Use multipartite layout for DAGs
                        layers = {}
                        for node in nx.topological_sort(G):
                            # Calculate layer based on longest path from source
                            predecessors = list(G.predecessors(node))
                            if not predecessors:
                                layers[node] = 0
                            else:
                                layers[node] = max(layers[pred] for pred in predecessors) + 1
                        
                        # Group nodes by layer
                        from collections import defaultdict
                        layer_groups = defaultdict(list)
                        for node, layer in layers.items():
                            layer_groups[layer].append(node)
                        
                        # Use multipartite layout
                        for layer, nodes in layer_groups.items():
                            for node in nodes:
                                G.nodes[node]['layer'] = layer
                        
                        pos = nx.multipartite_layout(G, subset_key='layer', scale=scale)
                    else:
                        # Use shell layout for cyclic graphs
                        pos = nx.shell_layout(G, scale=scale)
                except Exception:
                    # Fallback to spring layout
                    pos = nx.spring_layout(G, k=2.0/num_nodes**0.5, iterations=100, scale=scale)
            else:  # circular
                pos = nx.circular_layout(G, scale=scale)
            
            # Apply positions. For 'good' layout we rely on grid and skip collision adjustment
            # to preserve the deterministic MLP grid layout as computed by _compute_good_layout.
            min_distance = 100  # Minimum distance used for collision detection when needed
            
            for node, (x, y) in pos.items():
                if node not in self.node_items:
                    continue
                # Use direct snapped placement for Good Layout to preserve grid design
                if layout_type == 'good':
                    try:
                        if getattr(self, 'snap_to_grid', False) and getattr(self, 'grid_size', 0) > 0:
                            x, y = self.snap_point(x, y, step=self.snap_step)
                    except Exception:
                        pass
                    self.node_items[node].setPos(x, y)
                    continue

                # For other layouts, apply collision detection/adjustment
                adjusted_x, adjusted_y = x, y
                max_attempts = 50
                for attempt in range(max_attempts):
                    collision = False
                    for other_node, other_item in self.node_items.items():
                        if other_node == node:
                            continue
                        other_pos = other_item.pos()
                        dx = adjusted_x - other_pos.x()
                        dy = adjusted_y - other_pos.y()
                        distance = (dx**2 + dy**2)**0.5
                        if distance < min_distance:
                            collision = True
                            # Push away from collision (mild push)
                            if distance > 0:
                                push_x = (dx / distance) * (min_distance - distance)
                                push_y = (dy / distance) * (min_distance - distance)
                                adjusted_x += push_x * 0.5
                                adjusted_y += push_y * 0.5
                    if not collision:
                        break
                self.node_items[node].setPos(adjusted_x, adjusted_y)

            # Post-processing for Good Layout: ensure input buffers (Buff_xN) are placed
            # to the right of the corresponding input (xN) with at least one unit offset.
            if layout_type == 'good':
                try:
                    unit = getattr(self, 'grid_size', 20) * getattr(self, 'snap_step', 4)
                    for name, item in self.node_items.items():
                        nm = getattr(name, 'name', str(name))
                        if nm.startswith('Buff_x'):
                            # Parse index
                            import re
                            m = re.match(r'Buff_x(\d+)', nm)
                            if not m:
                                continue
                            idx = int(m.group(1))
                            # Find corresponding x node
                            x_node = next((n for n in self.node_items.keys() if getattr(n,'name',None) == f'x{idx}'), None)
                            if not x_node:
                                continue
                            x_item = self.node_items[x_node]
                            # Ensure buffer is to the right by at least one unit
                            bx, by = item.pos().x(), item.pos().y()
                            tx = x_item.pos().x() + unit
                            if bx <= x_item.pos().x():
                                item.setPos(tx, by)
                    # Ensure multiplication nodes are to the right of their weight predecessors
                    for n, item in list(self.node_items.items()):
                        nm2 = getattr(n, 'name', str(n))
                        if nm2.startswith('Mul_'):
                            # Try to find a ContainerNode or weight predecessor
                            preds = getattr(n, 'predecessors', []) if hasattr(n, 'predecessors') else []
                            weight_pred = None
                            for p in preds:
                                pn = getattr(p, 'name', str(p))
                                if pn.startswith('W_') or pn.startswith('wn') or pn.startswith('wx'):
                                    weight_pred = p
                                    break
                            if weight_pred and weight_pred in self.node_items:
                                wx = self.node_items[weight_pred].pos().x()
                                mx, my = item.pos().x(), item.pos().y()
                                if mx <= wx:
                                    item.setPos(wx + unit, my)
                    # Ensure activation nodes are to the right of their Add nodes
                    import re
                    for n, item in list(self.node_items.items()):
                        nm2 = getattr(n, 'name', str(n))
                        if nm2.startswith('Act_'):
                            m = re.match(r'Act_(?:L|H)(\d+)N(\d+)', nm2)
                        else:
                            m = None
                        if not m:
                            continue
                            L = int(m.group(1))
                            N = int(m.group(2))
                            # find corresponding Add_L{L}N{N}
                            add_node = next((a for a in self.node_items.keys() if getattr(a, 'name', None) in (f'Add_L{L}N{N}', f'Add_H{L}N{N}')), None)
                            if add_node and add_node in self.node_items:
                                ax, ay = item.pos().x(), item.pos().y()
                                addx = self.node_items[add_node].pos().x()
                                if ax <= addx:
                                    item.setPos(addx + unit, ay)
                    # Ensure derivative nodes for hidden layers are placed below their buffer nodes
                    for n, item in list(self.node_items.items()):
                        nm2 = getattr(n, 'name', str(n))
                        if nm2.startswith('D_H'):
                            m = re.match(r'D_H(\d+)N(\d+)', nm2)
                            if not m:
                                continue
                            L = int(m.group(1))
                            N = int(m.group(2))
                            buff_node = next((b for b in self.node_items.keys() if getattr(b, 'name', None) == f'Buff_H{L}N{N}'), None)
                            if buff_node and buff_node in self.node_items:
                                bx, by = self.node_items[buff_node].pos().x(), self.node_items[buff_node].pos().y()
                                dx, dy = item.pos().x(), item.pos().y()
                                if dy <= by:
                                    item.setPos(dx, by + unit)
                except Exception:
                    pass
            
            # Update all edges
            for edge_item in self.edge_items:
                edge_item.update_position()
            
            # Update scene rect to encompass all nodes with padding
            self._update_scene_rect()
            
            # Apply ANN colors if using ANN layout
            if layout_type == "ann":
                self.apply_ann_colors()
        
        except ImportError:
            print("NetworkX not installed. Install with: pip install networkx")
    
    def _compute_ann_layout(self, G, scale):
        """
        Compute ANN-specific left-to-right layout.
        
        Strategy:
        - Layer 0: Input streams (x nodes) and Label streams (Label_ or yd nodes)
        - Layer 1: First multiplication nodes (Mul_x)
        - Layer 2: Weight container nodes (W_x, wn_, wx_)
        - Layer 3: Hidden layer addition nodes (Add_L)
        - Layer 4: Hidden layer activation nodes (Act_L, Sigmoid, ReLU, etc.)
        - Layer 5: Hidden layer derivatives (D_H, derivative nodes)
        - Layer 6+: Repeat for additional hidden layers
        - Layer N-3: Output addition nodes (Add_y)
        - Layer N-2: Output activation nodes (y nodes, output activations)
        - Layer N-1: Error nodes (Error_, e nodes)
        - Layer N: Backprop gradient nodes (EG_, LRMult_, dW_)
        - Special: LearningRate node at top
        """
        from collections import defaultdict
        import re
        
        # Categorize nodes by type and layer
        layers = defaultdict(list)
        node_names = {node: node.name if hasattr(node, 'name') else str(node) for node in G.nodes()}
        
        for node in G.nodes():
            name = node_names[node]
            
            # Layer 0: Input and Label streams
            if name.startswith('x') and 'Stream' in name:
                layers[0].append(node)
            elif name.startswith('L_y') or name.startswith('yd') or name.startswith('Label_'):
                layers[0].append(node)
            
            # Layer 0.5: Weight containers (before multiplication, will be positioned behind with offset)
            elif name.startswith('W_x') or name.startswith('wx') or name.startswith('wn'):
                layers[0.5].append(node)
            
            # Layer 1: First multiplication (Input × Weight)
            elif name.startswith('Mul_x'):
                layers[1].append(node)
            
            # Layer 3-N: Hidden layers (dynamically detect layer number)
            elif name.startswith('Add_L'):
                # Extract layer number from name like "Add_L0N1"
                match = re.search(r'Add_L(\d+)', name)
                if match:
                    h_layer = int(match.group(1))
                    layers[3 + h_layer * 3].append(node)
            
            elif name.startswith('Act_L') or (name.startswith('n') and 'Sigmoid' in name):
                # Activation nodes
                match = re.search(r'H(\d+)', name)
                if match:
                    h_layer = int(match.group(1))
                    layers[4 + h_layer * 3].append(node)
            
            elif name.startswith('D_H'):
                # Derivative nodes
                match = re.search(r'D_H(\d+)', name)
                if match:
                    h_layer = int(match.group(1))
                    layers[5 + h_layer * 3].append(node)
            
            # Output layer
            elif name.startswith('Add_y'):
                layers[100].append(node)  # Use high number, will renumber later
            
            elif name.startswith('y') and not name.startswith('yd'):
                # Output activation nodes
                layers[101].append(node)
            
            # Error nodes
            elif name.startswith('Error_') or name.startswith('e') and 'E' in name:
                layers[102].append(node)
            
            # Backprop nodes - assign to same layer as their forward counterpart
            elif name.startswith('EG_'):
                # Error gradient nodes align with their layer
                match = re.search(r'EG_H(\d+)', name) or re.search(r'EG_y', name)
                if match and 'H' in name:
                    h_layer = int(re.search(r'H(\d+)', name).group(1))
                    layers[4 + h_layer * 3].append(node)  # Same layer as activation
                else:
                    layers[101].append(node)  # Output layer EG
            elif name.startswith('LRMult_') or name.startswith('WGS_'):
                # Learning rate mult nodes align with their layer
                match = re.search(r'H(\d+)', name)
                if match:
                    h_layer = int(match.group(1))
                    layers[4 + h_layer * 3].append(node)
                else:
                    layers[101].append(node)
            elif name.startswith('dW_') or name.startswith('dw_'):
                # Weight gradient nodes align with weight layer
                layers[0.5].append(node)
            
            # Learning rate (special positioning)
            elif name == 'LearningRate' or name == 'LR':
                layers[-1].append(node)  # Special layer
            
            # Fallback: use graph topology
            else:
                # Calculate layer based on longest path from inputs
                try:
                    predecessors = list(G.predecessors(node))
                    if not predecessors:
                        layers[0].append(node)
                    else:
                        # Find max layer of predecessors
                        pred_layers = []
                        for layer_num, layer_nodes in layers.items():
                            for pred in predecessors:
                                if pred in layer_nodes:
                                    pred_layers.append(layer_num)
                        if pred_layers:
                            layers[max(pred_layers) + 1].append(node)
                        else:
                            layers[50].append(node)  # Unknown layer
                except Exception:
                    layers[50].append(node)
        
        # Compress layers to sequential positions but maintain a reverse mapping
        sorted_layers = sorted([k for k in layers.keys() if k >= 0])
        layer_map = {old: new for new, old in enumerate(sorted_layers)}
        
        # reverse_layer_map is unused (kept for reference if needed)
        
        # Add learning rate layer at the end
        if -1 in layers:
            layer_map[-1] = len(sorted_layers)
        
        # Compute positions with diagonal backprop layout
        pos = {}
        layer_width = 200  # Horizontal spacing between layers
        node_spacing = 80  # Vertical spacing between nodes
        diagonal_offset_x = 50  # Horizontal diagonal offset
        diagonal_offset_y = 60  # Vertical diagonal offset
        
        # First, position all forward pass nodes normally (excluding label nodes)
        for old_layer, nodes in layers.items():
            new_layer = layer_map.get(old_layer, 0)
            x = new_layer * layer_width
            
            # Separate by node type for special positioning
            for node in nodes:
                name = node_names[node]
                
                # Skip backprop nodes and label nodes for now
                if any(pattern in name for pattern in ['EG_', 'LRMult_', 'dW_', 'dw_', 'WGS_', 'WG_', 'Label_', 'yd']):
                    continue
                
                # Calculate base position
                layer_nodes = [n for n in nodes if not any(p in node_names[n] for p in ['EG_', 'LRMult_', 'dW_', 'dw_', 'WGS_', 'WG_', 'Label_', 'yd'])]
                node_index = layer_nodes.index(node) if node in layer_nodes else 0
                num_nodes = len(layer_nodes)
                y = -(num_nodes - 1) * node_spacing / 2 + node_index * node_spacing
                
                # Special positioning rules
                if name.startswith('W_'):  # Weight nodes
                    x -= diagonal_offset_x  # Slightly left of Mult nodes
                    y -= 120  # Above Mult nodes
                elif name.startswith('D_') or 'Derivative' in name or 'derivative' in name:  # Derivative nodes
                    # Find corresponding activation node to position relative to it
                    x += diagonal_offset_x  # Upper-right of activation
                    y -= diagonal_offset_y
                
                pos[node] = (x, y)
        
        # Now position backprop nodes with diagonal offsets
        # First, group dW nodes by their target layer
        dw_by_target_layer = {}
        for old_layer, nodes in layers.items():
            for node in nodes:
                name = node_names[node]
                if name.startswith('dW_') or name.startswith('dw_'):
                    # Parse dW node name to determine which layer it updates
                    # Format: dW_x{input}H{layer}N{neuron} or dW_H{layer}N{neuron}y{output}
                    target_layer = 0.5  # Default to weight layer
                    
                    if 'H' in name and 'y' not in name:
                        # dW for input to hidden: dW_x0H0N1 -> layer 0.5 (before layer 1 Mult)
                        target_layer = 0.5
                    elif 'H' in name and 'y' in name:
                        # dW for hidden to output: dW_H0N1y0 -> position above hidden layer
                        match = re.search(r'H(\d+)', name)
                        if match:
                            h_layer = int(match.group(1))
                            target_layer = 4 + h_layer * 3  # Align with hidden activation layer
                    
                    if target_layer not in dw_by_target_layer:
                        dw_by_target_layer[target_layer] = []
                    dw_by_target_layer[target_layer].append(node)
        
        # Position dW nodes above their target layers
        for target_layer, dw_nodes in dw_by_target_layer.items():
            target_x = layer_map.get(target_layer, 0) * layer_width
            for node_idx, node in enumerate(dw_nodes):
                x = target_x - diagonal_offset_x * 0.5  # Midpoint between W and Mult
                y = -250 - node_idx * 100  # Diagonal cascade with more spacing
                pos[node] = (x, y)
        
        # Group other backprop nodes by their target layer
        lrmult_by_layer = {}
        eg_by_layer = {}
        wgs_by_layer = {}
        
        for old_layer, nodes in layers.items():
            for node in nodes:
                name = node_names[node]
                
                # Skip dW nodes (already positioned)
                if name.startswith('dW_') or name.startswith('dw_'):
                    continue
                
                # LRMult nodes: parse to find target layer
                elif name.startswith('LRMult_') or name.startswith('LRML_'):
                    target_layer = 0.5  # Default
                    if 'H' in name and 'y' not in name:
                        target_layer = 0.5
                    elif 'H' in name and 'y' in name:
                        match = re.search(r'H(\d+)', name)
                        if match:
                            h_layer = int(match.group(1))
                            target_layer = 4 + h_layer * 3
                    if target_layer not in lrmult_by_layer:
                        lrmult_by_layer[target_layer] = []
                    lrmult_by_layer[target_layer].append(node)
                
                # EG nodes: position above their activation layer
                elif name.startswith('EG_'):
                    target_layer = 101  # Default to output
                    if 'H' in name:
                        match = re.search(r'H(\d+)', name)
                        if match:
                            h_layer = int(match.group(1))
                            target_layer = 4 + h_layer * 3
                    if target_layer not in eg_by_layer:
                        eg_by_layer[target_layer] = []
                    eg_by_layer[target_layer].append(node)
                
                # WGS/WG nodes: align with their EG layer
                elif name.startswith('WGS_') or name.startswith('WG_'):
                    target_layer = 101  # Default to output
                    if 'H' in name:
                        match = re.search(r'H(\d+)', name)
                        if match:
                            h_layer = int(match.group(1))
                            target_layer = 4 + h_layer * 3
                    if target_layer not in wgs_by_layer:
                        wgs_by_layer[target_layer] = []
                    wgs_by_layer[target_layer].append(node)
        
        # Position LRMult nodes above their target layers
        for target_layer, lrmult_nodes in lrmult_by_layer.items():
            target_x = layer_map.get(target_layer, 0) * layer_width
            for node_idx, node in enumerate(lrmult_nodes):
                x = target_x - diagonal_offset_x - 30
                y = -350 - node_idx * 100
                pos[node] = (x, y)
        
        # Position EG nodes above their target layers
        for target_layer, eg_nodes in eg_by_layer.items():
            target_x = layer_map.get(target_layer, 0) * layer_width
            for node_idx, node in enumerate(eg_nodes):
                x = target_x + diagonal_offset_x
                y = -250 - node_idx * 100
                pos[node] = (x, y)
        
        # Position WGS/WG nodes horizontally aligned with EG
        for target_layer, wgs_nodes in wgs_by_layer.items():
            target_x = layer_map.get(target_layer, 0) * layer_width
            for node_idx, node in enumerate(wgs_nodes):
                x = target_x + diagonal_offset_x + 20
                y = -250 - node_idx * 100
                pos[node] = (x, y)
        
        # Learning Rate node: centered above everything
        if -1 in layers:
            lr_node = layers[-1][0]
            # Find middle layer
            mid_layer = len(sorted_layers) // 2
            x = mid_layer * layer_width
            y = -450  # High above everything
            pos[lr_node] = (x, y)
        
        # Finally, position label nodes below their corresponding error nodes
        for old_layer, nodes in layers.items():
            for node in nodes:
                name = node_names[node]
                if name.startswith('Label_') or name.startswith('yd'):
                    # Extract label index (e.g., L_y0 -> 0)
                    label_match = re.search(r'y(\d+)', name)
                    if label_match:
                        label_idx = label_match.group(1)
                        # Find corresponding error node across all layers
                        error_name = f'Error_y{label_idx}'
                        error_node = None
                        for layer_nodes in layers.values():
                            for n in layer_nodes:
                                if node_names[n] == error_name:
                                    error_node = n
                                    break
                            if error_node:
                                break
                        # Position below error if found
                        if error_node and error_node in pos:
                            x = pos[error_node][0]
                            y = pos[error_node][1] + 120  # Directly below
                            pos[node] = (x, y)
                        else:
                            # Fallback: position at output layer
                            output_layer = layer_map.get(101, len(sorted_layers) - 1)
                            x = output_layer * layer_width
                            y = 150
                            pos[node] = (x, y)
        
        return pos

    def _compute_good_layout(self, G, scale):
        """
        Compute the new 'Good' MLP layout. Uses a cellular grid where each cell
        is the node size plus padding. Lays out nodes deterministically left-to-right
        through input -> buffers -> weights -> mults -> additions -> activations -> buffer.

        Algorithm (simplified and robust):
        - Detect input nodes `x{idx}` and place them in column 0 vertically
        - For `Buff_x{idx}` place them at column 1, same row as their x
        - For first-layer weights `W_x{i}H0N{j}`, place in column 2 and row=j
        - Multiplication nodes `Mul_x{i}H{j}` are column 3 and row=j
        - Addition nodes `Add_L0N{j}` at column 4 and row=j, activation `Act_L0N{j}` at column 5
        - Repeat for additional hidden layers; weights between hidden layers are placed in
          columns offset by a group width per layer (group width = 5)
        - Output layer is interpreted as last group's addition/activation
        - Buffer nodes are placed after their activation in same column as buffer slot
        - Derivative nodes (D_H*) are placed at (buffer_col + 1, buffer_row + 1)

        It is intentionally deterministic and grid-based to align neurons and their
        connecting weight/multiplication nodes vertically by neuron index.
        """
        import re
        from collections import defaultdict

        node_names = {node: getattr(node, 'name', str(node)) for node in G.nodes()}

        # Helpers
        def match_name(pattern, name):
            return re.match(pattern, name)

        # Discover patterns: categorize nodes into forward-pass groups and buffers/derivatives
        inputs = []  # list of (node, idx)
        buffs_x = {}  # idx -> Buff node
        weights = defaultdict(list)  # key -> list of (node, i, j)
        muls = []
        adds = defaultdict(list)  # layer -> list of (node, neuron_idx)
        acts = defaultdict(list)
        buffs_h = defaultdict(list)  # layer -> list of (node, neuron_idx)
        derivatives = []
        outputs_add = []
        outputs_act = []

        for node in G.nodes():
            name = node_names[node]
            m = match_name(r'^x(\d+)$', name)
            if m:
                inputs.append((node, int(m.group(1))))
                continue
            m = match_name(r'^Buff_x(\d+)$', name)
            if m:
                buffs_x[int(m.group(1))] = node
                continue
            m = match_name(r'^W_x(\d+)H(\d+)N(\d+)$', name)
            if m:
                i = int(m.group(1))
                layer = int(m.group(2))
                j = int(m.group(3))
                weights[(layer, f'x{i}')].append((node, i, j))
                continue
            m = match_name(r'^W_H(\d+)N(\d+)H(\d+)N(\d+)$', name)
            if m:
                from_layer = int(m.group(1))
                i = int(m.group(2))
                to_l = int(m.group(3))
                j = int(m.group(4))
                weights[(to_l, f'H{from_layer}')].append((node, i, j))
                continue
            m = match_name(r'^Mul_([A-Za-z].+)$', name)
            if m:
                muls.append(node)
                continue
            m = match_name(r'^Add_(?:L|H)(\d+)N(\d+)$', name)
            if m:
                layer = int(m.group(1))
                n = int(m.group(2))
                adds[layer].append((node, n))
                continue
            m = match_name(r'^Act_(?:L|H)(\d+)N(\d+)$', name)
            if m:
                layer = int(m.group(1))
                n = int(m.group(2))
                acts[layer].append((node, n))
                continue
            m = match_name(r'^Buff_H(\d+)N(\d+)$', name)
            if m:
                layer = int(m.group(1))
                n = int(m.group(2))
                buffs_h[layer].append((node, n))
                continue
            m = match_name(r'^D_H(\d+)N(\d+)$', name)
            if m:
                layer = int(m.group(1))
                n = int(m.group(2))
                derivatives.append((node, layer, n))
                continue
            m = match_name(r'^D_y(\d+)$', name)
            if m:
                derivatives.append((node, 'y', int(m.group(1))))
                continue
            m = match_name(r'^Add_y(\d+)$', name)
            if m:
                outputs_add.append((node, int(m.group(1))))
                continue
            m = match_name(r'^y(\d+)$', name)
            if m:
                outputs_act.append((node, int(m.group(1))))
                continue

        # Determine grid dimensions
        # Number of grid steps reserved per hidden layer (columns per layer)
        step_per_layer = 8
        num_hidden_layers = max(adds.keys()) + 1 if adds else 0
        max_hidden_neurons = max((max([n for (_, n) in nodes]) + 1) if nodes else 0 for nodes in adds.values()) if adds else 0
        max_rows = max([len(inputs), max_hidden_neurons, len(outputs_add)])
        if max_rows == 0:
            max_rows = 1

        # Determine cell size using canvas grid settings when available.
        try:
            # unit equals node-sized step (grid_size * snap_step usually equals node diameter)
            grid_unit = int(getattr(self, 'grid_size', 20)) * int(getattr(self, 'snap_step', 4))
            cell_w = grid_unit
            cell_h = grid_unit
        except Exception:
            # Fallback to previous manual calculation
            radii = [item.radius for item in self.node_items.values() if hasattr(item, 'radius')]
            avg_radius = sum(radii) / len(radii) if radii else 40
            cell_w = avg_radius * 2 + 40
            cell_h = avg_radius * 2 + 40

        # Map grid cell (col, row) -> pixel pos
        max_columns = 2 + (num_hidden_layers + 1) * step_per_layer + 2

        def cell_to_pixel(col, row):
            # Simplified deterministic mapping; use top-left origin for grid.
            x = col * cell_w
            y = row * cell_h
            # Snap final coordinates to grid if grid snapping enabled
            try:
                if getattr(self, 'snap_to_grid', False) and getattr(self, 'grid_size', 0) > 0:
                    x, y = self.snap_point(x, y, step=self.snap_step)
            except Exception:
                pass
            return (x, y)

        pos = {}

        # Place inputs and input buffers
        for node, idx in inputs:
            row = idx
            pos[node] = cell_to_pixel(0, row)
            buff = buffs_x.get(idx)
            if buff:
                # Place input buffer top-right of its input if possible
                # If this would fall outside grid (row == 0), place it at row +1 instead
                buff_row = row - 1 if row > 0 else row + 1
                pos[buff] = cell_to_pixel(1, buff_row)

        # Hidden layer placements (add/act/buff)
        for layer, nodes in adds.items():
            for (node, n) in nodes:
                base = 2 + (layer * step_per_layer)
                pos[node] = cell_to_pixel(base + 2, n)
        for layer, nodes in acts.items():
            for (node, n) in nodes:
                base = 2 + (layer * step_per_layer)
                pos[node] = cell_to_pixel(base + 3, n)
        for layer, nodes in buffs_h.items():
            for (node, n) in nodes:
                base = 2 + (layer * step_per_layer)
                # Place hidden layer buffer top-right of activation if possible
                # Place hidden buffer top-right (above) activation if possible
                # If at top row then place below so it remains distinct
                buff_row = n - 1 if n > 0 else n + 1
                pos[node] = cell_to_pixel(base + 4, buff_row)

        # Weights and multiplications
        # To avoid stacking multiple weight nodes for the same target neuron j,
        # distribute the weights vertically across nearby rows centered at j.
        weight_row_map = {}  # node -> row assigned
        weight_col_map = {}  # node -> column assigned
        for key, wlist in weights.items():
            # group by target neuron j
            grouped_by_j = defaultdict(list)
            for (node, i, j) in wlist:
                grouped_by_j[j].append((node, i, j))
            for j, items in grouped_by_j.items():
                # Sort by source index (i) to make distribution deterministic
                items_sorted = sorted(items, key=lambda x: x[1])
                c = len(items_sorted)
                # Center rows around the neuron index j
                start_row = j - (c - 1) // 2
                for idx_in_group, (node, i, j2) in enumerate(items_sorted):
                    row = start_row + idx_in_group
                    target_layer = key[0] if isinstance(key[0], int) else 0
                    base = 2 + ((max(0, target_layer - 1)) * step_per_layer) if target_layer > 0 else 2
                    # Column offset using target neuron j for diagonal cascading across neurons
                    col = base + j
                    pos[node] = cell_to_pixel(col, row)
                    weight_row_map[node] = row
                    weight_col_map[node] = col

        for node in muls:
            name = node_names[node]
            m = re.match(r'^Mul_x(\d+)H(\d+)$', name)
            if m:
                j = int(m.group(2))
                # Align the mul node based on the corresponding weight node row if available
                # find weight for pair (first layer weights) matching i/j
                i = int(m.group(1))
                # Search for matching weight node in weights[(0,'x')] list
                assigned_row = None
                if (0, 'x') in weights:
                    for (wn, si, sj) in weights[(0, 'x')]:
                        if si == i and sj == j:
                            assigned_row = weight_row_map.get(wn)
                            assigned_col = weight_col_map.get(wn)
                            break
                row = assigned_row if assigned_row is not None else j
                col = (assigned_col + 1) if assigned_row is not None and 'assigned_col' in locals() else 3
                pos[node] = cell_to_pixel(col, row)
                continue
            m = re.match(r'^Mul_H(\d+)N(\d+)H(\d+)N(\d+)$', name)
            if m:
                to_l = int(m.group(3))
                j = int(m.group(4))
                # Align with corresponding weight row for hidden->hidden muls
                i = int(m.group(2))
                assigned_row = None
                assigned_col = None
                key = (to_l, f'H{to_l-1}' )
                if key in weights:
                    for (wn, si, sj) in weights[key]:
                        if si == i and sj == j:
                            assigned_row = weight_row_map.get(wn)
                            assigned_col = weight_col_map.get(wn)
                            break
                base = 2 + ((to_l - 1) * step_per_layer)
                row = assigned_row if assigned_row is not None else j
                col = (assigned_col + 1) if assigned_col is not None else base + 1
                pos[node] = cell_to_pixel(col, row)
                continue
            m = re.match(r'^Mul_H(\d+)N(\d+)y(\d+)$', name)
            if m:
                from_l = int(m.group(1))
                j = int(m.group(3))
                base = 2 + ((from_l) * step_per_layer)
                pos[node] = cell_to_pixel(base + 1, j)
                continue
            # fallback
            pos[node] = cell_to_pixel(3, 0)

        # Output positions
        last_group_base = 2 + (num_hidden_layers * step_per_layer)
        for (node, idx) in outputs_add:
            pos[node] = cell_to_pixel(last_group_base + 2, idx)
        for (node, idx) in outputs_act:
            pos[node] = cell_to_pixel(last_group_base + 3, idx)

        # Derivatives placed relative to corresponding buffers
        for (node, layer, n) in derivatives:
            if layer == 'y':
                col = last_group_base + 4
                row = n
            else:
                base = 2 + (layer * step_per_layer)
                col = base + 5
                row = n + 1
            pos[node] = cell_to_pixel(col, row)

        return pos
    
    def _update_scene_rect(self):
        """Update scene rect to encompass all nodes with padding."""
        if not self.node_items:
            return
        
        # Find bounds of all nodes
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        for node_item in self.node_items.values():
            pos = node_item.pos()
            radius = node_item.radius
            
            min_x = min(min_x, pos.x() - radius)
            max_x = max(max_x, pos.x() + radius)
            min_y = min(min_y, pos.y() - radius)
            max_y = max(max_y, pos.y() + radius)
        
        # Add padding (500 pixels on each side for comfortable panning)
        padding = 500
        min_x -= padding
        max_x += padding
        min_y -= padding
        max_y += padding
        
        # Update scene rect
        width = max_x - min_x
        height = max_y - min_y
        self.scene.setSceneRect(min_x, min_y, width, height)
    
    def apply_ann_colors(self):
        """
        Apply ANN-specific color scheme to nodes.
        
        Color scheme:
        - White: Input streams, activations, additions, multiplication (forward pass)
        - Blue: Weights (W_*, wn_*, wx_*), LR, dW nodes, weight-related multiplications
        - Green: Activation derivatives (D_*, *derivative), their multiplications
        - Red: Label streams, Error nodes
        - Purple/Pink: Backprop gradient nodes (EG_*, LRMult_*, WGS_*)
        """
        
        for node, node_item in self.node_items.items():
            name = node.name if hasattr(node, 'name') else str(node)
            color = None
            
            # Red: Label streams and Error nodes
            if name.startswith('Label_') or name.startswith('yd') or name.startswith('Error_') or (name.startswith('e') and 'E' in name):
                color = QColor(180, 60, 60)  # Dark red
            
            # Blue: Weights, LR, dW nodes
            elif (name.startswith('W_') or name.startswith('wn') or name.startswith('wx') or 
                  name == 'LearningRate' or name == 'LR' or name.startswith('dW_')):
                color = QColor(60, 100, 180)  # Dark blue
            
            # Yellow/Gold: Buffer nodes
            elif 'Buff' in name or 'Buffer' in name or 'buffer' in name:
                color = QColor(200, 149, 62)  # Yellow/Gold #c8953e
            
            # Green: Activation derivatives and their multiplications
            elif name.startswith('D_') or 'derivative' in name.lower() or 'Derivative' in name:
                color = QColor(60, 150, 60)  # Dark green
            
            # Purple: Backprop gradient nodes (EG, LRMult, WGS, weighted gradients)
            elif (name.startswith('EG_') or name.startswith('LRMult_') or name.startswith('WGS_') or 
                  name.startswith('WG_') or name.startswith('Weighted')):
                color = QColor(120, 80, 150)  # Dark purple
            
            # Gray: Everything else (inputs, activations, additions, forward multiplications)
            else:
                color = QColor(100, 100, 100)  # Dark gray (instead of white)
            
            # Apply the color to the node item
            if color:
                node_item.color = color
                node_item.update()  # Force redraw
