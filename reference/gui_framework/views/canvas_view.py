"""
Canvas View - PyQt6 QGraphicsView for rendering computational graphs.

This is the Stage 1 (Rendering) implementation focusing on displaying
nodes and edges from the CanvasViewModel. Interaction will be added in Stage 2.
"""

from typing import Dict, Optional

try:
    from PyQt6.QtCore import QPointF, QRectF, Qt
    from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
    from PyQt6.QtWidgets import (
        QGraphicsEllipseItem,
        QGraphicsItem,
        QGraphicsPathItem,
        QGraphicsScene,
        QGraphicsTextItem,
        QGraphicsView,
    )

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


if PYQT_AVAILABLE:
    from gui_framework.viewmodels.canvas_viewmodel import (
        CanvasViewModel,
        EdgeRenderState,
        NodeRenderState,
    )
    from gui_framework.views.base import BaseView

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
            self.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True
            )  # Stage 2: enable dragging
            self.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True
            )  # Stage 2: enable selection
            self.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True
            )  # Stage 2: notify position changes
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

            # Store reference to canvas view for callbacks (set by CanvasView)
            self.canvas_view = None

        def itemChange(self, change, value):
            """Handle item changes (position, selection)."""
            if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
                # Stage 3: Track position when drag starts
                if (
                    self.canvas_view
                    and not self.canvas_view._node_drag_start_positions.get(
                        self.node_id
                    )
                ):
                    current_pos = self.scenePos()
                    self.canvas_view._node_drag_start_positions[self.node_id] = (
                        current_pos.x(),
                        current_pos.y(),
                    )

            elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
                # Notify canvas view of position change
                if self.canvas_view:
                    new_pos = value  # QPointF
                    self.canvas_view._on_node_moved(
                        self.node_id, new_pos.x(), new_pos.y()
                    )

                # Update connected edges
                for edge in self.scene().items():
                    if isinstance(edge, EdgeItemView):
                        if edge.source_item == self or edge.target_item == self:
                            edge.update_position()

            elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
                # Update selection highlight
                if value:  # Selected
                    self.setPen(QPen(QColor(255, 255, 0), 3))  # Yellow highlight
                else:  # Deselected
                    self.setPen(QPen(Qt.GlobalColor.black, 2))

            return super().itemChange(change, value)

        def mouseReleaseEvent(self, event):
            """Handle mouse release to create undo command for move."""
            super().mouseReleaseEvent(event)

            # Stage 3: Create undo command when drag ends
            if self.canvas_view:
                self.canvas_view._on_node_drag_ended()

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

        def __init__(
            self,
            edge_state: EdgeRenderState,
            source_item: NodeItemView,
            target_item: NodeItemView,
        ):
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
            self.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False
            )  # Stage 1: no selection

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

        Stage 1 (Rendering): Displays nodes and edges from ViewModel. ✅ COMPLETE
        Stage 2 (Interaction): Node drag/drop, selection, rubber band. ✅ COMPLETE
        Stage 3 (Commands): Undo/redo with QUndoStack integration. ✅ COMPLETE
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
            self.view.setDragMode(
                QGraphicsView.DragMode.RubberBandDrag
            )  # Stage 2: enable rubber band selection

            # Node and edge item tracking
            self._node_items: Dict[str, NodeItemView] = {}
            self._edge_items: Dict[str, EdgeItemView] = {}

            # Interaction state
            self._drag_start_pos = None
            self._node_drag_start_positions: Dict[str, tuple] = (
                {}
            )  # Stage 3: track drag start for undo

            # Stage 3: Undo/Redo support
            try:
                from PyQt6.QtGui import QUndoStack

                self.undo_stack = QUndoStack(self)
                self.undo_stack.setUndoLimit(50)  # Limit undo history
            except ImportError:
                self.undo_stack = None

            self._setup_ui()
            # Ensure binding happens after UI initialization so the view
            # can immediately reflect current ViewModel state (useful for tests)
            try:
                self._bind_viewmodel()
            except Exception:
                # Fall back to scheduled binding (BaseView) if immediate bind fails
                pass

        def _setup_ui(self):
            """Setup the canvas UI."""
            # Use view as the main widget (this is a wrapper)
            from PyQt6.QtWidgets import QVBoxLayout

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.view)

            # Connect scene selection changes to ViewModel sync
            self.scene.selectionChanged.connect(self._on_selection_changed)

        def _bind_viewmodel(self):
            """Bind to viewmodel properties."""
            self._viewmodel.observe_property("nodes_changed", self._on_nodes_changed)
            self._viewmodel.observe_property("edges_changed", self._on_edges_changed)
            self._viewmodel.observe_property(
                "viewport_changed", self._on_viewport_changed
            )

            # Initialize UI from current ViewModel state so views created after
            # ViewModel initialization reflect current graph immediately.
            try:
                self._render_nodes()
                self._render_edges()
                self._on_viewport_changed(None, None)
            except Exception:
                pass

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

        def _on_selection_changed(self):
            """Handle scene selection changed event."""
            self._sync_selection_to_viewmodel()

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
                    item = self._node_items[node_state.node_id]
                    item.update_state(node_state)
                    # Update selection state
                    item.setSelected(node_state.is_selected)
                else:
                    # Create new node
                    item = NodeItemView(node_state)
                    item.canvas_view = self  # Set callback reference
                    self.scene.addItem(item)
                    self._node_items[node_state.node_id] = item
                    # Set initial selection state
                    item.setSelected(node_state.is_selected)

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

        def _on_node_moved(self, node_id: str, x: float, y: float):
            """
            Callback when a node is moved by user drag.

            Args:
                node_id: Node that was moved
                x, y: New position
            """
            self._viewmodel.update_node_position(node_id, x, y)

        def _on_node_drag_ended(self):
            """
            Called when node drag ends. Creates an undo command for the move.

            Stage 3: Integrates with QUndoStack for undo/redo support.
            """
            if not self.undo_stack or not self._node_drag_start_positions:
                return

            # Build position changes
            node_positions = {}
            for node_id, (old_x, old_y) in self._node_drag_start_positions.items():
                node_state = self._viewmodel.get_node(node_id)
                if node_state:
                    new_x, new_y = node_state.x, node_state.y
                    # Only create command if position actually changed
                    if abs(new_x - old_x) > 0.1 or abs(new_y - old_y) > 0.1:
                        node_positions[node_id] = (old_x, old_y, new_x, new_y)

            # Clear drag tracking
            self._node_drag_start_positions.clear()

            # Create and push undo command
            if node_positions:
                from gui_framework.commands import MoveNodesCommand

                command = MoveNodesCommand(self._viewmodel, node_positions)
                self.undo_stack.push(command)
                print(
                    f"[CanvasView] Created undo command for {len(node_positions)} moved nodes"
                )

        def _sync_selection_to_viewmodel(self):
            """Synchronize scene selection to ViewModel."""
            # Get selected items from scene
            selected_items = self.scene.selectedItems()

            selected_node_ids = set()
            selected_edge_ids = set()

            for item in selected_items:
                if isinstance(item, NodeItemView):
                    selected_node_ids.add(item.node_id)
                elif isinstance(item, EdgeItemView):
                    selected_edge_ids.add(item.edge_id)

            # Update ViewModel if selection changed
            current_nodes = set(self._viewmodel.get_selected_nodes())
            current_edges = set(self._viewmodel.get_selected_edges())

            if selected_node_ids != current_nodes or selected_edge_ids != current_edges:
                # Clear and re-select
                self._viewmodel.clear_selection()

                for node_id in selected_node_ids:
                    self._viewmodel.select_node(node_id, add_to_selection=True)

                for edge_id in selected_edge_ids:
                    self._viewmodel.select_edge(edge_id, add_to_selection=True)

        def keyPressEvent(self, event):
            """Handle keyboard events."""
            from PyQt6.QtCore import Qt as QtCore

            # Undo/Redo shortcuts
            if (
                event.key() == QtCore.Key.Key_Z
                and event.modifiers() & QtCore.KeyboardModifier.ControlModifier
            ):
                if self.undo_stack:
                    if event.modifiers() & QtCore.KeyboardModifier.ShiftModifier:
                        # Ctrl+Shift+Z = Redo
                        if self.undo_stack.canRedo():
                            self.undo_stack.redo()
                            print(f"[CanvasView] Redo: {self.undo_stack.redoText()}")
                    else:
                        # Ctrl+Z = Undo
                        if self.undo_stack.canUndo():
                            self.undo_stack.undo()
                            print(f"[CanvasView] Undo: {self.undo_stack.undoText()}")
                event.accept()
                return

            # Ctrl+Y = Redo (alternative)
            if (
                event.key() == QtCore.Key.Key_Y
                and event.modifiers() & QtCore.KeyboardModifier.ControlModifier
            ):
                if self.undo_stack and self.undo_stack.canRedo():
                    self.undo_stack.redo()
                    print(f"[CanvasView] Redo: {self.undo_stack.redoText()}")
                event.accept()
                return

            # Delete selected items
            if event.key() in (QtCore.Key.Key_Delete, QtCore.Key.Key_Backspace):
                selected_nodes = self._viewmodel.get_selected_nodes()
                selected_edges = self._viewmodel.get_selected_edges()
                if selected_nodes or selected_edges:
                    print(
                        f"[CanvasView] Delete key: {len(selected_nodes)} nodes, {len(selected_edges)} edges"
                    )
                    # Stage 3: Create delete command (placeholder - needs graph model integration)
                    if self.undo_stack:
                        from gui_framework.commands import DeleteItemsCommand

                        command = DeleteItemsCommand(
                            self._viewmodel, selected_nodes, selected_edges
                        )
                        self.undo_stack.push(command)
                event.accept()
                return

            # Select all
            if (
                event.key() == QtCore.Key.Key_A
                and event.modifiers() & QtCore.KeyboardModifier.ControlModifier
            ):
                for item in self._node_items.values():
                    item.setSelected(True)
                self._sync_selection_to_viewmodel()
                event.accept()
                return

            super().keyPressEvent(event)

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
