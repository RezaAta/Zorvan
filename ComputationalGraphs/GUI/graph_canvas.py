"""
QGraphicsView-based canvas for displaying and editing the computational graph.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView

from .edge_item import EdgeItem
from .node_item import NodeItem


class GraphCanvas(QGraphicsView):
    """Interactive canvas for node graph editing."""

    node_selected = pyqtSignal(object)  # Emits the selected node
    edge_created = pyqtSignal(object, object)  # Emits (source_node, target_node)
    edge_removed = pyqtSignal(
        object, object
    )  # Emits (source_node, target_node) when an edge is removed
    # Emitted when a connection drag operation is released on empty space.
    # Args: scene position (QPointF), list of NodeItem objects that started the connection
    connection_dropped_on_empty = pyqtSignal(object, object)

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
        # (No spacebar panning state) - use only middle-button panning
        # Auto-expand canvas when nodes are added/removed
        self.auto_expand_to_nodes = True
        # Default scene rect and padding
        try:
            self.default_scene_rect = self.scene.sceneRect()
        except Exception:
            self.default_scene_rect = self.scene.sceneRect()
        self.canvas_padding = 500

        # Grid / snap settings
        self.node_diameter = 80  # Default assumed diameter (2 * radius 40)
        self.grid_mode = (
            "1x1"  # '1x1' (grid cell) or '4x4' - default to 1x1 for MLP layouts
        )
        self.grid_size = (
            self.node_diameter
        )  # 80px for 1x1 mode (one grid cell = one node)
        self.grid_major_every = 4  # draw a major line every 4 cells (node size)
        self.grid_minor_color = QColor(45, 45, 45)
        self.grid_major_color = QColor(70, 70, 70)
        self.show_grid = False
        # Default to no grid snapping (preserve manual node positions typical for user layout)
        self.snap_to_grid = False
        self.snap_while_dragging = (
            True  # default: snap while dragging so users see snap live
        )
        self.snap_step = 1  # Snap in units of grid cells (1 for 1x1 mode)

        # Node tracking
        self.node_items = {}  # Maps node objects to NodeItem widgets
        self.edge_items = []
        # Internal clipboard for copy/paste
        self._clipboard = None
        # Track whether ANN colors are currently applied on the canvas
        self.ann_colors_active = False

    def add_node_item(self, node, x=0, y=0):
        """Add a visual representation of a node to the canvas."""
        # snap initial position if enabled
        try:
            if (
                getattr(self, "snap_to_grid", False)
                and getattr(self, "grid_size", 0) > 0
            ):
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
            if not hasattr(node_item, "value_label") or node_item.value_label is None:
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
        # If ANN colors are active, compute and apply color to the newly added node
        try:
            if getattr(self, "ann_colors_active", False):
                color = self._ann_color_for_node(
                    node.name if hasattr(node, "name") else str(node)
                )
                if color is not None:
                    # Use set_manual_color helper to update node color
                    try:
                        node_item.set_manual_color(color)
                    except Exception:
                        try:
                            node_item.manual_color = color
                            node_item.update()
                        except Exception:
                            pass
        except Exception:
            # If we can't apply colors for some reason, ignore and continue
            pass
        # If requested, auto-expand the scene rect to include the new node
        try:
            if getattr(self, "auto_expand_to_nodes", False):
                self._update_scene_rect()
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
            node_diam = getattr(self, "node_diameter", 80)
            if mode == "1x1":
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
        if not getattr(self, "snap_to_grid", False):
            return x, y
        if getattr(self, "grid_size", 0) <= 0:
            return x, y
        try:
            s = int(step or getattr(self, "snap_step", 1))
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
        if not getattr(self, "show_grid", False):
            return
        # grid size in pixels
        g = getattr(self, "grid_size", 20)
        if g <= 0:
            return

        import math

        from PyQt6.QtGui import QPainter, QPen

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
                if hasattr(self, "graph") and getattr(self, "graph") is not None:
                    # Only connect if the nodes belong to the authoritative graph
                    try:
                        if target_node in getattr(
                            self.graph, "nodes", []
                        ) and source_node in getattr(self.graph, "nodes", []):
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
            # Handle node item deletion
            if isinstance(item, NodeItem):
                # Remove connected edges first
                for edge in list(item.edges[:]):
                    # Safely compute the associated graph nodes
                    try:
                        src = edge.source_node.node
                        tgt = edge.target_node.node
                    except Exception:
                        continue

                    # Emit removal signal to listeners
                    try:
                        self.edge_removed.emit(src, tgt)
                    except Exception:
                        pass

                    # Disconnect in authoritative graph if available
                    try:
                        if (
                            hasattr(self, "graph")
                            and getattr(self, "graph") is not None
                        ):
                            self.graph.DisconnectPreNode(tgt, src)
                    except Exception:
                        pass

                    # Remove the visual edge and its internal record
                    try:
                        # Prefer the EdgeItem removal helper
                        edge.remove()
                    except Exception:
                        try:
                            self.scene.removeItem(edge)
                        except Exception:
                            pass
                    try:
                        if edge in self.edge_items:
                            self.edge_items.remove(edge)
                    except Exception:
                        pass
                # Now remove the node item itself
                try:
                    if item in self.node_items.values():
                        # remove scene item
                        self.scene.removeItem(item)
                        # remove mapping
                        to_remove = None
                        for n, i in list(self.node_items.items()):
                            if i == item:
                                to_remove = n
                                break
                        if to_remove is not None:
                            del self.node_items[to_remove]
                except Exception:
                    pass
            # Continue to remove all selected items rather than returning early
            # (The earlier early return prevented removing more than one selection)
            # Handle edge item deletion (selected edge directly)
            from .edge_item import EdgeItem

            if isinstance(item, EdgeItem):
                try:
                    src = item.source_node.node
                    tgt = item.target_node.node
                except Exception:
                    src = None
                    tgt = None
                # Disconnect in authoritative graph if available
                try:
                    if (
                        hasattr(self, "graph")
                        and getattr(self, "graph") is not None
                        and src is not None
                        and tgt is not None
                    ):
                        self.graph.DisconnectPreNode(tgt, src)
                except Exception:
                    pass
                # Remove the visual edge and internal record
                try:
                    item.remove()
                except Exception:
                    try:
                        self.scene.removeItem(item)
                    except Exception:
                        pass
                try:
                    if item in self.edge_items:
                        self.edge_items.remove(item)
                except Exception:
                    pass

        # Update scene rect if auto-expand is enabled, but do NOT refit the view
        # (Refitting the view on every delete is disorienting for the user)
        if getattr(self, "auto_expand_to_nodes", False):
            self._update_scene_rect()

    def delete_selected_with_undo(self):
        """Remove selected nodes and edges with undo support.

        Creates a RemoveItemsCommand and pushes it to the undo stack.
        """
        selected = self.scene.selectedItems()
        if not selected:
            return

        # Separate nodes and edges
        node_items = [item for item in selected if isinstance(item, NodeItem)]
        edge_items = [item for item in selected if isinstance(item, EdgeItem)]

        if not node_items and not edge_items:
            return

        # Get the undo stack from the main window
        undo_stack = self._get_undo_stack()
        if undo_stack is None:
            # Fallback to direct removal if no undo stack available
            self.remove_selected_items()
            return

        # Get the graph reference
        graph = getattr(self, "graph", None)
        if graph is None:
            self.remove_selected_items()
            return

        # Create and push the command
        from .commands import RemoveItemsCommand
        cmd = RemoveItemsCommand(self, graph, node_items, edge_items)
        undo_stack.push(cmd)

    def _get_undo_stack(self):
        """Get the undo stack from the main window if available."""
        try:
            # The parent of GraphCanvas should be the MainWindow
            main_window = self.parent()
            if main_window and hasattr(main_window, "undo_stack"):
                return main_window.undo_stack
        except Exception:
            pass
        return None

    def add_edge_with_undo(self, source_node, target_node):
        """Add an edge between two nodes with undo support."""
        undo_stack = self._get_undo_stack()
        graph = getattr(self, "graph", None)

        if undo_stack is None or graph is None:
            # Fallback to direct add
            return self.add_edge_item(source_node, target_node)

        from .commands import AddEdgeCommand
        cmd = AddEdgeCommand(self, graph, source_node, target_node)
        undo_stack.push(cmd)

    def add_node_with_undo(self, node, x, y):
        """Add a node to the canvas with undo support."""
        undo_stack = self._get_undo_stack()
        graph = getattr(self, "graph", None)

        if undo_stack is None or graph is None:
            # Fallback: add directly
            if graph:
                graph.AddNode(node)
            return self.add_node_item(node, x, y)

        from .commands import AddNodeCommand
        cmd = AddNodeCommand(self, graph, node, x, y)
        undo_stack.push(cmd)

    def mousePressEvent(self, event):
        """Handle mouse press for panning with middle button."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Start panning
            self.panning = True
            self.pan_start_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
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
            return
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
                self.temp_connection_lines[i].setLine(
                    start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y()
                )
            return

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
                if (
                    isinstance(item, NodeItem)
                    and item not in self.connection_start_nodes
                ):
                    # Accept connection if released anywhere on the target node
                    target_node = item
                    break

            if target_node:
                # Create edges from all start nodes to this target (with undo support)
                for start in self.connection_start_nodes:
                    if start.node != target_node.node:
                        self.add_edge_with_undo(start.node, target_node.node)
            else:
                # Released on empty space: emit a signal so controller can open
                # a node-type search dialog and optionally create a new node
                try:
                    # Emit with the scene position and an explicit list copy
                    self.connection_dropped_on_empty.emit(
                        pos, list(self.connection_start_nodes)
                    )
                except Exception:
                    pass

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
            return

        super().mouseReleaseEvent(event)

    # (Spacebar panning feature removed) - keyboard events not used for panning.

    def wheelEvent(self, event):
        """Zoom view using mouse wheel.

        Zoom is anchored under the mouse pointer (set earlier with
        setTransformationAnchor). Clamps zoom between min and max scales to
        avoid making nodes too small or too large.
        """
        # Prefer angleDelta (most common); fallback to pixelDelta for trackpads
        delta = 0
        try:
            delta = event.angleDelta().y()
        except Exception:
            try:
                delta = event.pixelDelta().y()
            except Exception:
                delta = 0

        # If delta is 0, nothing to do -> pass to superclass
        if delta == 0:
            super().wheelEvent(event)
            return

        # Zoom factors: positive delta -> zoom in, negative -> zoom out
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        factor = zoom_in_factor if delta > 0 else zoom_out_factor

        # Enforce min/max scale
        current_scale = self.transform().m11()  # assume uniform scaling
        min_scale = 0.2
        max_scale = 4.0
        new_scale = current_scale * factor
        if new_scale < min_scale:
            factor = min_scale / current_scale
        elif new_scale > max_scale:
            factor = max_scale / current_scale

        self.scale(factor, factor)
        event.accept()

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
            from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
            from ComputationalGraphs.Nodes.BufferNode import BufferNode
            from ComputationalGraphs.Nodes.BulkTournamentNode import BulkTournamentNode
            from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
            from ComputationalGraphs.Nodes.CrossoverNode import CrossoverNode
            from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
            from ComputationalGraphs.Nodes.DeJongSphereNode import DeJongSphereNode
            from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
            from ComputationalGraphs.Nodes.DivisionNode import DivisionNode
            from ComputationalGraphs.Nodes.DynamicDataStreamNode import (
                DynamicDataStreamNode,
            )
            from ComputationalGraphs.Nodes.ExtractListElement import ExtractListElement
            from ComputationalGraphs.Nodes.GaussianNode import GaussianNode
            from ComputationalGraphs.Nodes.LinearNode import LinearNode
            from ComputationalGraphs.Nodes.ListNode import ListNode
            from ComputationalGraphs.Nodes.MaxNode import MaxNode
            from ComputationalGraphs.Nodes.MeanSquaredErrorNode import (
                MeanSquaredErrorNode,
            )
            from ComputationalGraphs.Nodes.MinNode import MinNode
            from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
            from ComputationalGraphs.Nodes.MutationNode import MutaionNode
            from ComputationalGraphs.Nodes.PiecewiseLinearNode import (
                PiecewiseLinearNode,
            )
            from ComputationalGraphs.Nodes.ReLUDerivativeNode import ReLUDerivativeNode
            from ComputationalGraphs.Nodes.ReLUNode import ReLUNode
            from ComputationalGraphs.Nodes.SequencerNode import SequencerNode
            from ComputationalGraphs.Nodes.SigmoidDerivativeNode import (
                SigmoidDerivativeNode,
            )
            from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
            from ComputationalGraphs.Nodes.SingleCrossoverNode import (
                SingleCrossoverNode,
            )
            from ComputationalGraphs.Nodes.SubtractionNode import SubtractionNode
            from ComputationalGraphs.Nodes.TanhDerivativeNode import TanhDerivativeNode
            from ComputationalGraphs.Nodes.TanhNode import TanhNode
            from ComputationalGraphs.Nodes.TournamentSelectionNode import (
                TournamentSelectionNode,
            )

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
                from ComputationalGraphs.Nodes.MovingAverageNode import (
                    MovingAverageNode,
                )

                node = MovingAverageNode(
                    name=f"MovAvg_{node_id}", size=10, mode="continuous"
                )
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
                # Use undo-aware add if available
                self.add_node_with_undo(node, drop_pos.x(), drop_pos.y())
                event.acceptProposedAction()

    # Note: _create_node_by_type and the earlier replace_node_item implementation were removed
    # in favor of the dynamic `replace_node_item()` implementation defined later in this file.

    def update_node_visuals(
        self, colorize=False, min_val=0, max_val=1, min_color=None, max_color=None
    ):
        """Update all node visuals (values and optionally colors).

        Note: This only clears value-based color (node_item.color), not manual_color
        which is set by ANN colors or user and persists across updates.
        """
        for node_item in self.node_items.values():
            node_item.update_value_display()
            if colorize:
                # When colorizing by value, ensure any ANN/manual colors are cleared
                try:
                    node_item.manual_color = None
                except Exception:
                    pass
                node_item.colorize_by_value(min_val, max_val, min_color, max_color)
            else:
                # When not colorizing by value: if ANN colors are active, keep manual_color
                if getattr(self, "ann_colors_active", False):
                    # ANN colors are persistent, clear value-based color only
                    node_item.color = None
                    node_item.update()
                else:
                    # Reset value-based color to None so paint() will use manual_color or default
                    # (manual_color will be None if not set)
                    node_item.color = None
                    node_item.update()

    def highlight_selected_nodes_for_connection(self, on: bool):
        """Highlight all currently selected nodes for connection preview."""
        selected_items = [
            item for item in self.scene.selectedItems() if isinstance(item, NodeItem)
        ]
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

    def start_connection(self, start_node_item):
        """Begin an interactive connection operation from the provided NodeItem.

        This places the canvas into connection_mode and highlights the start node
        or selected nodes if multiple are selected.
        """
        try:
            # Determine selected start nodes: use current selection if start_node_item is selected
            selected_items = [
                item
                for item in self.scene.selectedItems()
                if isinstance(item, NodeItem)
            ]
            if start_node_item in selected_items:
                self.connection_start_nodes = selected_items
            else:
                self.connection_start_nodes = [start_node_item]

            # Lock movement on the start node(s) and highlight
            for n in self.connection_start_nodes:
                try:
                    n.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                    n.set_connection_highlight(True)
                except Exception:
                    pass

            self.connection_mode = True
            self.temp_connection_lines = []
            # Disable rubber-band drag while connecting
            try:
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
            except Exception:
                pass
        except Exception:
            pass

    def _create_node_by_class_name(self, class_name, attrs=None):
        """Instantiate a node by its class name using dynamic inspection of the Nodes package.

        Args:
            class_name: The class name of the node to create (e.g., 'ContainerNode').
            attrs: Optional dict of attributes to pass to constructor and/or set after creation.

        Returns the new node or None.
        """
        import importlib
        import inspect
        import pkgutil

        try:
            import ComputationalGraphs.Nodes as NodesPkg

            cls = None

            # First try the direct package exports
            for name, obj in inspect.getmembers(NodesPkg):
                if inspect.isclass(obj) and obj.__name__ == class_name:
                    cls = obj
                    break

            # If not found in exports, scan all submodules
            if cls is None:
                for importer, modname, ispkg in pkgutil.iter_modules(NodesPkg.__path__):
                    try:
                        module = importlib.import_module(
                            f"ComputationalGraphs.Nodes.{modname}"
                        )
                        if hasattr(module, class_name):
                            cls = getattr(module, class_name)
                            break
                    except Exception:
                        continue

            if cls is None:
                print(
                    f"[Copy/Paste] Warning: Class '{class_name}' not found in Nodes package"
                )
                return None

            # Attribute-to-parameter mappings for nodes where stored attribute names
            # differ from constructor parameter names
            attr_to_param_mappings = {
                "BufferNode": {"buffer": "data", "bufferSize": "size"},
                "DataStreamNode": {
                    "streamIndex": None
                },  # None means skip this attr for constructor
            }

            # Build constructor kwargs from attrs that match constructor parameters
            constructor_kwargs = {}
            if attrs:
                try:
                    sig = inspect.signature(cls.__init__)
                    param_names = set(sig.parameters.keys()) - {"self"}
                    mappings = attr_to_param_mappings.get(class_name, {})

                    for attr_name, attr_val in attrs.items():
                        # Check if this attribute maps to a different parameter name
                        if attr_name in mappings:
                            param_name = mappings[attr_name]
                            if param_name is None:
                                continue  # Skip this attribute
                        else:
                            param_name = attr_name

                        # Only include if parameter exists in constructor
                        if param_name in param_names:
                            constructor_kwargs[param_name] = attr_val
                except Exception:
                    # Fallback: just try 'name' if available
                    if "name" in attrs:
                        constructor_kwargs["name"] = attrs["name"]

            # Create the node
            try:
                new_node = cls(**constructor_kwargs) if constructor_kwargs else cls()
            except Exception as e:
                # Fallback to empty constructor
                try:
                    new_node = cls()
                except Exception:
                    return None

            return new_node

        except Exception as e:
            print(f"[Copy/Paste] Error creating node '{class_name}': {e}")
            return None

    def _get_node_attributes(self, node):
        """Extract all serializable attributes from a node for copying.

        Excludes internal/private attributes, predecessors, inputs, and callable methods.
        Similar approach to CGJsonIO._get_node_attributes.
        """
        import inspect
        from copy import deepcopy

        attrs = {}
        for attr_name, val in vars(node).items():
            # Skip private/internal attributes
            if attr_name.startswith("_"):
                continue
            # Skip graph connection attributes (will be recreated)
            if attr_name in ("predecessors", "inputs", "id"):
                continue
            # Skip callable methods
            if inspect.isroutine(val):
                continue
            # Attempt to deepcopy the value
            try:
                attrs[attr_name] = deepcopy(val)
            except Exception:
                # For non-copyable values, try to use as-is or skip
                try:
                    attrs[attr_name] = val
                except Exception:
                    continue
        return attrs

    def _generate_unique_name(self, base_name):
        """Generate a unique node name by appending _copy or incrementing counter.

        Examples:
            'Node_1' -> 'Node_1_copy'
            'Node_1_copy' -> 'Node_1_copy2'
            'Node_1_copy2' -> 'Node_1_copy3'
        """
        if not base_name:
            base_name = "Node"

        existing_names = {n.name for n in self.node_items.keys() if hasattr(n, "name")}

        # If name doesn't exist yet, we can use it (but we still want to mark as copy)
        # Check if it already ends with _copy or _copyN
        import re

        copy_pattern = re.compile(r"^(.+?)_copy(\d*)$")
        match = copy_pattern.match(base_name)

        if match:
            # Already a copy, increment the counter
            root_name = match.group(1)
            counter_str = match.group(2)
            counter = int(counter_str) if counter_str else 1
            counter += 1
            candidate = f"{root_name}_copy{counter}"
        else:
            # First copy
            root_name = base_name
            candidate = f"{base_name}_copy"
            counter = 1

        # Ensure uniqueness
        while candidate in existing_names:
            counter += 1
            candidate = f"{root_name}_copy{counter}"

        return candidate

    def copy_selected(self):
        """Copy selected nodes and internal edges to the internal clipboard.

        Stores all node attributes (not just name/value/data) so that pasted
        nodes are true duplicates of the originals.
        """
        selected_items = [
            item for item in self.scene.selectedItems() if isinstance(item, NodeItem)
        ]
        if not selected_items:
            return

        nodes_info = []
        node_to_index = {}

        for idx, item in enumerate(selected_items):
            n = item.node
            node_to_index[n] = idx

            # Collect ALL node attributes
            attrs = self._get_node_attributes(n)

            node_info = {
                "class": type(n).__name__,
                "attrs": attrs,
                "gui_pos": (float(item.pos().x()), float(item.pos().y())),
            }
            nodes_info.append(node_info)

        # Collect internal edges between selected nodes
        edges = []
        for edge in list(self.edge_items):
            try:
                s = edge.source_node.node
                t = edge.target_node.node
                if s in node_to_index and t in node_to_index:
                    edges.append((node_to_index[s], node_to_index[t]))
            except Exception:
                pass

        self._clipboard = {"nodes": nodes_info, "edges": edges}

    def cut_selected(self):
        """Copy selected nodes then remove them from the canvas."""
        self.copy_selected()
        self.delete_selected_with_undo()

    def paste_clipboard(self):
        """Paste nodes and edges from the internal clipboard with undo support.

        Creates true duplicates of the copied nodes with all their attributes preserved.
        New nodes get unique names (with _copy suffix) and are placed at cursor position
        or viewport center, maintaining their relative positions to each other.
        """
        from copy import deepcopy

        from PyQt6.QtGui import QCursor

        if not self._clipboard:
            return

        nodes_info = self._clipboard.get("nodes", [])
        edges = self._clipboard.get("edges", [])
        if not nodes_info:
            return

        # Determine base position for paste - prefer cursor position if inside viewport
        try:
            global_pos = QCursor.pos()
            local_pos = self.mapFromGlobal(global_pos)
            if self.viewport().rect().contains(local_pos):
                scene_pos = self.mapToScene(local_pos)
                base_x = scene_pos.x()
                base_y = scene_pos.y()
            else:
                center = self.mapToScene(self.viewport().rect().center())
                base_x = center.x()
                base_y = center.y()
        except Exception:
            base_x = 0
            base_y = 0

        # Compute centroid of copied nodes to preserve relative positions
        gui_positions = [
            info.get("gui_pos") for info in nodes_info if info.get("gui_pos")
        ]
        if gui_positions:
            copy_center_x = sum(p[0] for p in gui_positions) / len(gui_positions)
            copy_center_y = sum(p[1] for p in gui_positions) / len(gui_positions)
        else:
            copy_center_x = 0
            copy_center_y = 0

        new_nodes = []
        node_positions = {}  # Track positions for undo command

        for idx, info in enumerate(nodes_info):
            class_name = info.get("class")
            attrs = info.get("attrs", {})

            # Generate unique name for the copy
            original_name = attrs.get("name", f"Node_{idx}")
            unique_name = self._generate_unique_name(original_name)

            # Update attrs with the unique name for constructor
            attrs_for_creation = deepcopy(attrs)
            attrs_for_creation["name"] = unique_name

            # Create the node with constructor-compatible attributes
            new_node = self._create_node_by_class_name(
                class_name, attrs=attrs_for_creation
            )

            if new_node is None:
                # Fallback: create a DisplayNode
                from ComputationalGraphs.Nodes.DisplayNode import DisplayNode

                new_node = DisplayNode(name=unique_name)
                print(
                    f"[Copy/Paste] Warning: Could not create {class_name}, using DisplayNode"
                )

            # Set any remaining attributes that weren't handled by constructor
            for attr_name, attr_val in attrs.items():
                if attr_name == "name":
                    continue  # Already set with unique name
                try:
                    # Only set if the attribute exists on the node or is a known attribute
                    if hasattr(new_node, attr_name):
                        setattr(new_node, attr_name, deepcopy(attr_val))
                except Exception as e:
                    print(
                        f"[Copy/Paste] Warning: Could not set attribute '{attr_name}': {e}"
                    )

            # Add node to the authoritative graph if available
            if hasattr(self, "graph") and self.graph is not None:
                try:
                    self.graph.AddNode(new_node)
                except Exception as e:
                    print(f"[Copy/Paste] Warning: Could not add node to graph: {e}")

            # Calculate position - maintain relative positions from original
            gui_pos = info.get("gui_pos")
            if gui_pos:
                rel_x = gui_pos[0] - copy_center_x
                rel_y = gui_pos[1] - copy_center_y
                pos_x = base_x + rel_x
                pos_y = base_y + rel_y
            else:
                # Fallback grid positioning
                pos_x = base_x + (idx % 5) * 40
                pos_y = base_y + (idx // 5) * 40

            self.add_node_item(new_node, pos_x, pos_y)
            new_nodes.append(new_node)
            node_positions[new_node] = (pos_x, pos_y)

        # Recreate internal edges between pasted nodes
        pasted_edges = []
        for s_idx, t_idx in edges:
            try:
                s_node = new_nodes[s_idx]
                t_node = new_nodes[t_idx]
                self.add_edge_item(s_node, t_node)
                pasted_edges.append((s_node, t_node))
            except Exception as e:
                print(f"[Copy/Paste] Warning: Could not recreate edge: {e}")

        # Select newly pasted nodes for better UX
        for it in list(self.scene.selectedItems()):
            it.setSelected(False)

        for n in new_nodes:
            ni = self.node_items.get(n)
            if ni:
                ni.setSelected(True)

        # Push undo command for the paste operation
        undo_stack = self._get_undo_stack()
        graph = getattr(self, "graph", None)
        if undo_stack is not None and graph is not None and new_nodes:
            from .commands import PasteCommand
            cmd = PasteCommand(self, graph, new_nodes, pasted_edges, node_positions)
            undo_stack.push(cmd)

    def apply_layout(self, layout_type="spring"):
        """No-op layout plumbing: preserve method signature for compatibility.

        Replaces the previous GUI layout algorithms with a minimal implementation
        that updates edges and optionally reapplies ANN colorization. This allows
        the UI to request layout without executing any heavy algorithm code.
        """
        if not self.node_items:
            return {}
        pos = {}
        try:
            # Construct a positions mapping based on gui_pos (if present) or current item positions
            for node, item in self.node_items.items():
                try:
                    if hasattr(node, "gui_pos") and node.gui_pos is not None:
                        # node.gui_pos may be tuple/list-like; coerce to (x,y)
                        if (
                            isinstance(node.gui_pos, (tuple, list))
                            and len(node.gui_pos) >= 2
                        ):
                            pos[node] = (float(node.gui_pos[0]), float(node.gui_pos[1]))
                        else:
                            pos[node] = (float(item.pos().x()), float(item.pos().y()))
                    else:
                        pos[node] = (float(item.pos().x()), float(item.pos().y()))
                except Exception:
                    # Fallback to current item pos
                    try:
                        pos[node] = (float(item.pos().x()), float(item.pos().y()))
                    except Exception:
                        pos[node] = (0.0, 0.0)

            if layout_type == "ann":
                self.apply_ann_colors()

            # Refresh edges and update the scene rect
            for edge_item in self.edge_items:
                try:
                    edge_item.update_position()
                except Exception:
                    pass
            self._update_scene_rect()
        except Exception:
            # swallow exceptions from layout plumbing to keep GUI stable; return partial pos mapping
            pass

        return pos

    def _compute_ann_layout(self, G, scale):
        """ANN layout removed: compatibility stub.

        Returns a mapping of nodes to their existing GUI positions if available,
        else returns (0.0, 0.0) default positions. Keeps API stable for callers.
        """
        pos = {}
        for node in G.nodes():
            if hasattr(node, "gui_pos") and node.gui_pos is not None:
                pos[node] = tuple(node.gui_pos)
            else:
                pos[node] = (0.0, 0.0)
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

        node_names = {node: getattr(node, "name", str(node)) for node in G.nodes()}

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
            m = match_name(r"^x(\d+)$", name)
            if m:
                inputs.append((node, int(m.group(1))))
                continue
            m = match_name(r"^Buff_x(\d+)$", name)
            if m:
                buffs_x[int(m.group(1))] = node
                continue
            m = match_name(r"^W_x(\d+)H(\d+)N(\d+)$", name)
            if m:
                i = int(m.group(1))
                layer = int(m.group(2))
                j = int(m.group(3))
                weights[(layer, f"x{i}")].append((node, i, j))
                continue
            m = match_name(r"^W_H(\d+)N(\d+)H(\d+)N(\d+)$", name)
            if m:
                from_layer = int(m.group(1))
                i = int(m.group(2))
                to_l = int(m.group(3))
                j = int(m.group(4))
                weights[(to_l, f"H{from_layer}")].append((node, i, j))
                continue
            m = match_name(r"^Mul_([A-Za-z].+)$", name)
            if m:
                muls.append(node)
                continue
            m = match_name(r"^Add_(?:L|H)(\d+)N(\d+)$", name)
            if m:
                layer = int(m.group(1))
                n = int(m.group(2))
                adds[layer].append((node, n))
                continue
            m = match_name(r"^Act_(?:L|H)(\d+)N(\d+)$", name)
            if m:
                layer = int(m.group(1))
                n = int(m.group(2))
                acts[layer].append((node, n))
                continue
            m = match_name(r"^Buff_H(\d+)N(\d+)$", name)
            if m:
                layer = int(m.group(1))
                n = int(m.group(2))
                buffs_h[layer].append((node, n))
                continue
            m = match_name(r"^D_H(\d+)N(\d+)$", name)
            if m:
                layer = int(m.group(1))
                n = int(m.group(2))
                derivatives.append((node, layer, n))
                continue
            m = match_name(r"^D_y(\d+)$", name)
            if m:
                derivatives.append((node, "y", int(m.group(1))))
                continue
            m = match_name(r"^Add_y(\d+)$", name)
            if m:
                outputs_add.append((node, int(m.group(1))))
                continue
            m = match_name(r"^y(\d+)$", name)
            if m:
                outputs_act.append((node, int(m.group(1))))
                continue

        # Determine grid dimensions
        # Number of grid steps reserved per hidden layer (columns per layer)
        step_per_layer = 8
        num_hidden_layers = max(adds.keys()) + 1 if adds else 0
        max_hidden_neurons = (
            max(
                (max([n for (_, n) in nodes]) + 1) if nodes else 0
                for nodes in adds.values()
            )
            if adds
            else 0
        )
        max_rows = max([len(inputs), max_hidden_neurons, len(outputs_add)])
        if max_rows == 0:
            max_rows = 1

        # Determine cell size using canvas grid settings when available.
        try:
            # unit equals node-sized step (grid_size * snap_step usually equals node diameter)
            grid_unit = int(getattr(self, "grid_size", 20)) * int(
                getattr(self, "snap_step", 4)
            )
            cell_w = grid_unit
            cell_h = grid_unit
        except Exception:
            # Fallback to previous manual calculation
            radii = [
                item.radius
                for item in self.node_items.values()
                if hasattr(item, "radius")
            ]
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
                if (
                    getattr(self, "snap_to_grid", False)
                    and getattr(self, "grid_size", 0) > 0
                ):
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
            for node, n in nodes:
                base = 2 + (layer * step_per_layer)
                pos[node] = cell_to_pixel(base + 2, n)
        for layer, nodes in acts.items():
            for node, n in nodes:
                base = 2 + (layer * step_per_layer)
                pos[node] = cell_to_pixel(base + 3, n)
        for layer, nodes in buffs_h.items():
            for node, n in nodes:
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
            for node, i, j in wlist:
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
                    base = (
                        2 + ((max(0, target_layer - 1)) * step_per_layer)
                        if target_layer > 0
                        else 2
                    )
                    # Column offset using target neuron j for diagonal cascading across neurons
                    col = base + j
                    pos[node] = cell_to_pixel(col, row)
                    weight_row_map[node] = row
                    weight_col_map[node] = col

        for node in muls:
            name = node_names[node]
            m = re.match(r"^Mul_x(\d+)H(\d+)$", name)
            if m:
                j = int(m.group(2))
                # Align the mul node based on the corresponding weight node row if available
                # find weight for pair (first layer weights) matching i/j
                i = int(m.group(1))
                # Search for matching weight node in weights[(0,'x')] list
                assigned_row = None
                if (0, "x") in weights:
                    for wn, si, sj in weights[(0, "x")]:
                        if si == i and sj == j:
                            assigned_row = weight_row_map.get(wn)
                            assigned_col = weight_col_map.get(wn)
                            break
                row = assigned_row if assigned_row is not None else j
                col = (
                    (assigned_col + 1)
                    if assigned_row is not None and "assigned_col" in locals()
                    else 3
                )
                pos[node] = cell_to_pixel(col, row)
                continue
            m = re.match(r"^Mul_H(\d+)N(\d+)H(\d+)N(\d+)$", name)
            if m:
                to_l = int(m.group(3))
                j = int(m.group(4))
                # Align with corresponding weight row for hidden->hidden muls
                i = int(m.group(2))
                assigned_row = None
                assigned_col = None
                key = (to_l, f"H{to_l-1}")
                if key in weights:
                    for wn, si, sj in weights[key]:
                        if si == i and sj == j:
                            assigned_row = weight_row_map.get(wn)
                            assigned_col = weight_col_map.get(wn)
                            break
                base = 2 + ((to_l - 1) * step_per_layer)
                row = assigned_row if assigned_row is not None else j
                col = (assigned_col + 1) if assigned_col is not None else base + 1
                pos[node] = cell_to_pixel(col, row)
                continue
            m = re.match(r"^Mul_H(\d+)N(\d+)y(\d+)$", name)
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
        for node, idx in outputs_add:
            pos[node] = cell_to_pixel(last_group_base + 2, idx)
        for node, idx in outputs_act:
            pos[node] = cell_to_pixel(last_group_base + 3, idx)

        # Derivatives placed relative to corresponding buffers
        for node, layer, n in derivatives:
            if layer == "y":
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
        min_x = float("inf")
        max_x = float("-inf")
        min_y = float("inf")
        max_y = float("-inf")

        for node_item in self.node_items.values():
            pos = node_item.pos()
            radius = node_item.radius

            min_x = min(min_x, pos.x() - radius)
            max_x = max(max_x, pos.x() + radius)
            min_y = min(min_y, pos.y() - radius)
            max_y = max(max_y, pos.y() + radius)

        # Add padding based on canvas setting
        padding = getattr(self, "canvas_padding", 500)
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

        These colors are set as manual_color, which persists across value-based
        color updates (colorize_by_value) and node visual refreshes.

        Color scheme:
        - Gray: Input streams, activations, additions, multiplication (forward pass)
        - Blue: Weights (W_*, wn_*, wx_*), LR, dW nodes, weight-related multiplications
        - Green: Activation derivatives (D_*, *derivative), their multiplications
        - Red: Label streams, Error nodes
        - Purple/Pink: Backprop gradient nodes (EG_*, LRMult_*, WGS_*)
        - Yellow/Gold: Buffer nodes
        """

        for node, node_item in self.node_items.items():
            name = node.name if hasattr(node, "name") else str(node)
            color = None

            # Red: Label streams and Error nodes
            if (
                name.startswith("Label_")
                or name.startswith("yd")
                or name.startswith("Error_")
                or (name.startswith("e") and "E" in name)
            ):
                color = QColor(180, 60, 60)  # Dark red

            # Blue: Weights, LR, dW nodes
            elif (
                name.startswith("W_")
                or name.startswith("wn")
                or name.startswith("wx")
                or name == "LearningRate"
                or name == "LR"
                or name.startswith("dW_")
            ):
                color = QColor(60, 100, 180)  # Dark blue

            # Yellow/Gold: Buffer nodes
            elif "Buff" in name or "Buffer" in name or "buffer" in name:
                color = QColor(200, 149, 62)  # Yellow/Gold #c8953e

            # Green: Activation derivatives and their multiplications
            elif (
                name.startswith("D_")
                or "derivative" in name.lower()
                or "Derivative" in name
            ):
                color = QColor(60, 150, 60)  # Dark green

            # Purple: Backprop gradient nodes (EG, LRMult, WGS, weighted gradients)
            elif (
                name.startswith("EG_")
                or name.startswith("LRMult_")
                or name.startswith("WGS_")
                or name.startswith("WG_")
                or name.startswith("Weighted")
            ):
                color = QColor(120, 80, 150)  # Dark purple

            # Gray: Everything else (inputs, activations, additions, forward multiplications)
            else:
                color = QColor(100, 100, 100)  # Dark gray (instead of white)

            # Apply the color using the node's helper
            if color:
                try:
                    node_item.set_manual_color(color)
                except Exception:
                    try:
                        node_item.manual_color = color
                        node_item.update()
                    except Exception:
                        pass
        # Mark that ANN colors are enabled on the canvas
        self.ann_colors_active = True

    def clear_ann_colors(self):
        """Clear all manual colors (ANN colors) from nodes, reverting to default colors."""
        for node_item in self.node_items.values():
            try:
                node_item.clear_manual_color()
            except Exception:
                try:
                    node_item.manual_color = None
                    node_item.update()
                except Exception:
                    pass
        # ANN colors are no longer active
        self.ann_colors_active = False

    def _ann_color_for_node(self, name: str):
        """Return the ANN color for a node name or None if not applicable.

        This function centralizes the color mapping logic used by apply_ann_colors and
        add_node_item.
        """
        import typing

        color = None
        try:
            # Red: Label streams and Error nodes
            if (
                name.startswith("Label_")
                or name.startswith("yd")
                or name.startswith("Error_")
                or (name.startswith("e") and "E" in name)
            ):
                color = QColor(180, 60, 60)  # Dark red
            elif (
                name.startswith("W_")
                or name.startswith("wn")
                or name.startswith("wx")
                or name == "LearningRate"
                or name == "LR"
                or name.startswith("dW_")
            ):
                color = QColor(60, 100, 180)  # Dark blue
            elif "Buff" in name or "Buffer" in name or "buffer" in name:
                color = QColor(200, 149, 62)  # Yellow/Gold #c8953e
            elif (
                name.startswith("D_")
                or "derivative" in name.lower()
                or "Derivative" in name
            ):
                color = QColor(60, 150, 60)  # Dark green
            elif (
                name.startswith("EG_")
                or name.startswith("LRMult_")
                or name.startswith("WGS_")
                or name.startswith("WG_")
                or name.startswith("Weighted")
            ):
                color = QColor(120, 80, 150)  # Dark purple
            else:
                color = QColor(100, 100, 100)  # Dark gray
        except Exception:
            color = None
        return color

    def fit_all_nodes_in_view(self):
        """Fit all nodes into the current view, maintaining aspect ratio."""
        if not self.node_items:
            return
        all_rects = [item.sceneBoundingRect() for item in self.node_items.values()]
        united_rect = all_rects[0]
        for rect in all_rects[1:]:
            united_rect = united_rect.united(rect)
        padding = max(united_rect.width(), united_rect.height()) * 0.1
        united_rect.adjust(-padding, -padding, padding, padding)
        try:
            self.fitInView(united_rect, Qt.AspectRatioMode.KeepAspectRatio)
        except Exception:
            pass

    def replace_node_item(self, node_item, new_type: str):
        """Replace the underlying graph node for a NodeItem with a new node instance of type new_type.

        Args:
            node_item: NodeItem instance to replace the underlying node for.
            new_type: String type name of the new node class (e.g., 'MultiplicationNode').

        Returns:
            The new node object if replacement succeeded, else None.
        """
        import inspect

        # find node class by name inside ComputationalGraphs.Nodes package
        try:
            import ComputationalGraphs.Nodes as NodesPkg

            cls = None
            for name, obj in inspect.getmembers(NodesPkg):
                if inspect.isclass(obj) and obj.__name__ == new_type:
                    cls = obj
                    break
            if cls is None:
                return None
            # Construct new node instance: prefer name parameter if supported
            kwargs = {}
            try:
                sig = inspect.signature(cls.__init__)
                if "name" in sig.parameters:
                    kwargs["name"] = getattr(node_item.node, "name", None)
            except Exception:
                pass
            try:
                new_node = cls(**kwargs) if kwargs else cls()
            except Exception:
                # fallback to empty constructor
                try:
                    new_node = cls()
                except Exception:
                    return None

            # If we have an authoritative graph, perform a Graph.ReplaceNode operation
            g = getattr(self, "graph", None)
            old_node = getattr(node_item, "node", None)
            if (
                g is not None
                and old_node is not None
                and old_node in getattr(g, "nodes", [])
            ):
                try:
                    g.ReplaceNode(new_node, old_node)
                except Exception:
                    # If graph replacement fails, abort
                    return None
            else:
                # No authoritative graph: attempt the simple replacement in canvas and mapping
                try:
                    # Keep visual mapping
                    if node_item in self.node_items.values():
                        # remove old mapping
                        to_remove = None
                        for n, i in list(self.node_items.items()):
                            if i == node_item:
                                to_remove = n
                                break
                        if to_remove is not None:
                            del self.node_items[to_remove]
                        self.node_items[new_node] = node_item
                except Exception:
                    pass

            # Update node_item reference to new node
            try:
                node_item.node = new_node
                # Update label text
                try:
                    node_item.set_label_text(getattr(new_node, "name", ""))
                except Exception:
                    pass
                # update value display
                try:
                    node_item.update_value_display()
                except Exception:
                    pass
            except Exception:
                pass

            # Return new node to caller
            return new_node
        except Exception:
            return None
