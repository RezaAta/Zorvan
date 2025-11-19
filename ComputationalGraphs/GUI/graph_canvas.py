"""
QGraphicsView-based canvas for displaying and editing the computational graph.
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor
from .node_item import NodeItem
from .edge_item import EdgeItem


class GraphCanvas(QGraphicsView):
    """Interactive canvas for node graph editing."""
    
    node_selected = pyqtSignal(object)  # Emits the selected node
    edge_created = pyqtSignal(object, object)  # Emits (source_node, target_node)
    
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
        
        # Node tracking
        self.node_items = {}  # Maps node objects to NodeItem widgets
        self.edge_items = []
        # Internal clipboard for copy/paste
        self._clipboard = None
        
    def add_node_item(self, node, x=0, y=0):
        """Add a visual representation of a node to the canvas."""
        node_item = NodeItem(node, x, y)
        self.scene.addItem(node_item)
        self.node_items[node] = node_item
        return node_item
    
    def add_edge_item(self, source_node, target_node):
        """Add a visual edge between two nodes."""
        source_item = self.node_items.get(source_node)
        target_item = self.node_items.get(target_node)
        
        if source_item and target_item:
            edge_item = EdgeItem(source_item, target_item)
            self.scene.addItem(edge_item)
            self.edge_items.append(edge_item)
            self.edge_created.emit(source_node, target_node)
            return edge_item
        
        return None
    
    def remove_selected_items(self):
        """Remove selected nodes and edges."""
        selected = self.scene.selectedItems()
        
        for item in selected:
            if isinstance(item, NodeItem):
                # Remove connected edges first
                for edge in item.edges[:]:
                    edge.remove()
                    if edge in self.edge_items:
                        self.edge_items.remove(edge)
                
                # Remove node item
                if item.node in self.node_items:
                    del self.node_items[item.node]
                
                self.scene.removeItem(item)
            
            elif isinstance(item, EdgeItem):
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
        from PyQt6.QtCore import QRectF
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
            
            # Apply positions with collision detection and adjustment
            min_distance = 100  # Minimum distance between node centers (nodes are ~80px diameter)
            
            for node, (x, y) in pos.items():
                if node in self.node_items:
                    # Check for collisions and adjust
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
                                # Push away from collision
                                if distance > 0:
                                    push_x = (dx / distance) * (min_distance - distance)
                                    push_y = (dy / distance) * (min_distance - distance)
                                    adjusted_x += push_x * 0.5
                                    adjusted_y += push_y * 0.5
                        
                        if not collision:
                            break
                    
                    self.node_items[node].setPos(adjusted_x, adjusted_y)
            
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
        - Layer 1: First multiplication nodes (Mult_x)
        - Layer 2: Weight container nodes (W_x, wn_, wx_)
        - Layer 3: Hidden layer addition nodes (Add_H)
        - Layer 4: Hidden layer activation nodes (Act_H, Sigmoid, ReLU, etc.)
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
            elif name.startswith('Label_') or name.startswith('yd'):
                layers[0].append(node)
            
            # Layer 0.5: Weight containers (before multiplication, will be positioned behind with offset)
            elif name.startswith('W_x') or name.startswith('wx') or name.startswith('wn'):
                layers[0.5].append(node)
            
            # Layer 1: First multiplication (Input × Weight)
            elif name.startswith('Mult_x'):
                layers[1].append(node)
            
            # Layer 3-N: Hidden layers (dynamically detect layer number)
            elif name.startswith('Add_H'):
                # Extract layer number from name like "Add_H0N1"
                match = re.search(r'Add_H(\d+)', name)
                if match:
                    h_layer = int(match.group(1))
                    layers[3 + h_layer * 3].append(node)
            
            elif name.startswith('Act_H') or (name.startswith('n') and 'Sigmoid' in name):
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
        
        # Create reverse map to find original layer numbers
        reverse_layer_map = {new: old for old, new in layer_map.items()}
        
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
                    # Extract label index (e.g., Label_y0 -> 0)
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
