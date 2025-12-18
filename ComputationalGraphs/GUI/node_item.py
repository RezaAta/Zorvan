"""
GraphicsItem representation of a computational graph node.
"""

import colorsys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QCursor, QFont, QPen
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QMenu,
    QStyle,
    QStyleOptionGraphicsItem,
)


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
        # Ensure nodes are drawn above edges
        try:
            self.setZValue(2)
        except Exception:
            pass

        # Disable caching to avoid trail artifacts
        self.setCacheMode(QGraphicsItem.CacheMode.NoCache)

        # Default colors - check if this is a CompressedNode or AbstractNode for distinct styling
        from ComputationalGraphs.Nodes.AbstractNode import AbstractNode
        from ComputationalGraphs.Nodes.CompressedNode import CompressedNode

        if isinstance(node, CompressedNode):
            # Gold/amber color for compressed nodes
            self.default_color = QColor(212, 160, 23)  # #D4A017 - gold
            self.selected_color = QColor(255, 200, 50)  # Lighter gold for selection
        elif isinstance(node, AbstractNode):
            # Purple color for abstract nodes
            self.default_color = QColor(155, 89, 182)  # #9B59B6 - purple
            self.selected_color = QColor(187, 143, 206)  # Lighter purple for selection
        else:
            # Use theme-managed default node color when available
            try:
                from .theme import get_theme_manager

                tm = get_theme_manager()
                self.default_color = tm.get_color("node_default", "#003fbd")
                # Selected color is a lighter variant of default
                self.selected_color = QColor(self.default_color).lighter(120)
                # Subscribe to theme changes to update default color dynamically
                tm.theme_changed.connect(self._on_theme_changed)
            except Exception:
                self.default_color = QColor(0, 63, 189)  # #003fbd
                self.selected_color = QColor(50, 113, 239)  # Lighter blue for selection

        # Track whether default_color was explicitly overridden by the
        # VisualizationController (apply_node_colors). If True, theme updates
        # should not overwrite the user-applied default color.
        self._default_color_overridden = False

        self.active_color = QColor(100, 180, 255)  # Bright light blue for active nodes
        self.color = None  # Custom color (set by layout/coloring functions)
        # Manual color is used for ANN/explicit coloring which takes precedence
        # over value-based coloring. Initialize to None for safety.
        self.manual_color = None
        self.is_active = (
            False  # Track if node is currently active (for Forward Processing)
        )
        self.setBrush(QBrush(self.default_color))
        self.setPen(QPen(Qt.GlobalColor.black, 2))

        # Label - for CompressedNode or AbstractNode, show node count
        if isinstance(node, CompressedNode):
            label_text = f"{node.name} [{len(node)}]"
        elif isinstance(node, AbstractNode):
            label_text = f"{node.name} [{len(node)}]"
        else:
            label_text = node.name
        # Label - prefer theme-managed node_text color when available
        try:
            from .theme import get_theme_manager

            tm = get_theme_manager()
            node_text_color = tm.get_color("node_text", "#ffffff")
            self.label = QGraphicsTextItem(label_text, self)
            self.label.setDefaultTextColor(node_text_color)
            tm.theme_changed.connect(self._on_theme_changed)
        except Exception:
            self.label = QGraphicsTextItem(label_text, self)
            self.label.setDefaultTextColor(Qt.GlobalColor.white)

        try:
            from .theme import get_theme_manager

            tm = get_theme_manager()
            node_font = tm.get_font("node")
            # make label bold while preserving family and size
            node_font.setBold(True)
            self.label.setFont(node_font)
        except Exception:
            font = QFont("Arial", 10, QFont.Weight.Bold)
            self.label.setFont(font)

        # Center the label
        label_rect = self.label.boundingRect()
        self.label.setPos(-label_rect.width() / 2, -label_rect.height() / 2 - 10)

        # Value display
        self.value_label = QGraphicsTextItem("", self)
        try:
            self.value_label.setDefaultTextColor(node_text_color)
        except Exception:
            self.value_label.setDefaultTextColor(Qt.GlobalColor.white)
        try:
            node_font = tm.get_font("node")
            value_font = node_font
            # Slightly smaller for value display
            value_font.setPointSize(max(6, node_font.pointSize() - 2))
            self.value_label.setFont(value_font)
        except Exception:
            value_font = QFont("Arial", 8)
            self.value_label.setFont(value_font)
        # Populate with initial value
        self.update_value_display()

        # Topology type label (displayed below the node, hidden by default)
        self.topology_label = QGraphicsTextItem("", self)
        try:
            # Topology label uses muted_text color so it's less prominent
            self.topology_label.setDefaultTextColor(
                tm.get_color("muted_text", "#a0a0a0")
            )
            topo_font = tm.get_font("node")
            topo_font.setPointSize(max(6, topo_font.pointSize() - 3))
            self.topology_label.setFont(topo_font)
        except Exception:
            self.topology_label.setDefaultTextColor(Qt.GlobalColor.lightGray)
            topology_font = QFont("Arial", 7, QFont.Weight.Normal)
            self.topology_label.setFont(topology_font)
        self.topology_label.setVisible(False)

        # Track move state to avoid unnecessary updates when clicking without movement
        self._moved = False
        self._pressed_pos = None
        self._move_start_scene_pos = None  # Track scene position at start of move

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
        if not hasattr(self, "value_label") or self.value_label is None:
            try:
                self.value_label = QGraphicsTextItem("", self)
                self.value_label.setDefaultTextColor(Qt.GlobalColor.white)
                value_font = QFont("Arial", 8)
                self.value_label.setFont(value_font)
            except Exception:
                # If creating the value label fails, skip updating the label
                return
        # For DataStreamNodes, show the data attribute if value is None
        if hasattr(self.node, "data") and self.node.value is None and self.node.data:
            # DataStreamNode with data but no value yet
            if isinstance(self.node.data, list) and len(self.node.data) > 0:
                display_text = f"[{len(self.node.data)} samples]"
            else:
                display_text = str(self.node.data)[:20]
        else:
            # For BufferNodes, show the delayed (oldest) output.
            # Avoid falling through to the generic formatting logic that expects `value` to be defined,
            # which causes an unbound-local error on the buffered branch.
            if hasattr(self.node, "buffer"):
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
                self.value_label.setPos(
                    -value_rect.width() / 2, value_rect.height() / 2
                )
                return
            else:
                value = self.node.value
            if value is None:
                display_text = "None"
            elif isinstance(value, (int, float)):
                display_text = (
                    f"{value:.2f}" if isinstance(value, float) else str(value)
                )
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

    def update_topology_label(self, show=True):
        """Update and show/hide the topology type label.

        Args:
            show: If True, display the topology label; if False, hide it.
        """
        if not hasattr(self, "topology_label") or self.topology_label is None:
            return

        if show:
            topo_type = getattr(self.node, "topology_type", None)
            if topo_type:
                self.topology_label.setPlainText(topo_type)
                # Position below the node circle
                rect = self.topology_label.boundingRect()
                self.topology_label.setPos(-rect.width() / 2, self.radius + 5)
                self.topology_label.setVisible(True)
            else:
                self.topology_label.setVisible(False)
        else:
            self.topology_label.setVisible(False)

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
            g = int(
                min_color.green() + (max_color.green() - min_color.green()) * normalized
            )
            b = int(
                min_color.blue() + (max_color.blue() - min_color.blue()) * normalized
            )

            self.color = QColor(r, g, b)
        elif isinstance(value, list):
            # Color based on list length (normalize to 0-10 range)
            normalized = min(len(value) / 10, 1.0)

            r = int(min_color.red() + (max_color.red() - min_color.red()) * normalized)
            g = int(
                min_color.green() + (max_color.green() - min_color.green()) * normalized
            )
            b = int(
                min_color.blue() + (max_color.blue() - min_color.blue()) * normalized
            )

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
                canvas = getattr(self, "canvas", None)
                # Fallback: attempt to get the view (GraphCanvas) assigned to the scene
                if canvas is None and self.scene() and self.scene().views():
                    try:
                        view = self.scene().views()[0]
                        # If the view is the GraphCanvas instance, use it
                        if hasattr(view, "snap_to_grid"):
                            canvas = view
                    except Exception:
                        pass
                if (
                    canvas
                    and getattr(canvas, "snap_to_grid", False)
                    and getattr(canvas, "snap_while_dragging", False)
                ):
                    # `value` is a QPointF with the proposed new position
                    from PyQt6.QtCore import QPointF

                    p = value
                    g = getattr(canvas, "grid_size", 0)
                    if g and g > 0:
                        step = getattr(canvas, "snap_step", 1)
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

            # Update subgraph control positions
            try:
                canvas = getattr(self, "canvas", None)
                if canvas is None and self.scene() and self.scene().views():
                    try:
                        view = self.scene().views()[0]
                        canvas = view
                    except Exception:
                        pass
                if canvas and hasattr(canvas, "update_subgraph_controls"):
                    canvas.update_subgraph_controls()
            except Exception:
                pass

            # Snap on release if enabled
            try:
                canvas = getattr(self, "canvas", None)
                # Fallback: attempt to get the view (GraphCanvas) assigned to the scene
                if canvas is None and self.scene() and self.scene().views():
                    try:
                        view = self.scene().views()[0]
                        if hasattr(view, "snap_to_grid"):
                            canvas = view
                    except Exception:
                        pass
                if (
                    canvas
                    and getattr(canvas, "snap_to_grid", False)
                    and not getattr(canvas, "snap_while_dragging", False)
                ):
                    # Snap to nearest unit after move completed
                    g = getattr(canvas, "grid_size", 0)
                    if g and g > 0:
                        step = getattr(canvas, "snap_step", 1)
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
                # Mark that the item has moved (used by mouseReleaseEvent to conditionally
                # trigger canvas rect updates)
                try:
                    self._moved = True
                except Exception:
                    pass
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
        # Reset moved flag on press and remember the pressed position
        try:
            self._moved = False
            self._pressed_pos = event.pos()
            # Store scene position at start of potential move for undo
            self._move_start_scene_pos = self.pos()
        except Exception:
            pass
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
                    if hasattr(view, "start_connection"):
                        view.start_connection(self)
                        event.accept()
                        return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        super().mouseReleaseEvent(event)
        # If the view is a GraphCanvas, ask it to update the scene rect after end of move
        try:
            scene = self.scene()
            if scene and scene.views():
                view = scene.views()[0]

                # Push undo command if the item actually moved
                if getattr(self, "_moved", False):
                    self._push_move_command(view)

                if hasattr(view, "_update_scene_rect") and getattr(
                    view, "auto_expand_to_nodes", False
                ):
                    try:
                        # Only trigger an update when the item actually moved
                        if getattr(self, "_moved", False):
                            view._update_scene_rect()
                    except Exception:
                        pass
                # Reset move tracking
                self._moved = False
                self._pressed_pos = None
                self._move_start_scene_pos = None
        except Exception:
            pass

    def _push_move_command(self, view):
        """Push a move command to the undo stack if available."""
        try:
            # Get the undo stack from the main window
            main_window = view.window()
            if not main_window or not hasattr(main_window, "undo_stack"):
                return

            undo_stack = main_window.undo_stack
            old_pos = getattr(self, "_move_start_scene_pos", None)
            if old_pos is None:
                return

            new_pos = self.pos()
            # Only push if position actually changed
            if (
                abs(old_pos.x() - new_pos.x()) < 0.1
                and abs(old_pos.y() - new_pos.y()) < 0.1
            ):
                return

            # Collect all selected nodes that moved together
            from .commands import MoveNodesCommand

            node_positions = []

            # Get all selected NodeItems from this item's scene
            scene = self.scene()
            if scene:
                selected_items = [
                    item for item in scene.selectedItems() if isinstance(item, NodeItem)
                ]

                # If this item is selected, include all selected items
                if self in selected_items:
                    for item in selected_items:
                        item_old_pos = getattr(item, "_move_start_scene_pos", None)
                        if item_old_pos is not None:
                            node_positions.append((item.node, item_old_pos, item.pos()))
                else:
                    # Just this item
                    node_positions.append((self.node, old_pos, new_pos))
            else:
                # No scene, just add this item
                node_positions.append((self.node, old_pos, new_pos))

            if node_positions:
                cmd = MoveNodesCommand(view, node_positions)
                undo_stack.push(cmd)
        except Exception:
            pass

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to open node editor."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get the view and open node editor
            scene = self.scene()
            if scene and scene.views():
                view = scene.views()[0]
                # Get the main window from the view
                main_window = view.window()
                if main_window and hasattr(main_window, "edit_node"):
                    main_window.edit_node(self)
                    event.accept()
                    return

        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        try:
            from ComputationalGraphs.Nodes.AbstractNode import AbstractNode
            from ComputationalGraphs.Nodes.CompressedNode import CompressedNode

            menu = QMenu()
            # View predecessors menu item
            view_pred_action = menu.addAction("View Predecessors")
            replace_action = menu.addAction("Replace Node...")
            menu.addSeparator()
            swallow_action = menu.addAction("Swallow Node")
            swallow_action.setToolTip(
                "Remove node while connecting predecessors to successors"
            )

            # Compression actions
            compress_action = None
            decompress_action = None

            # Check if this is a CompressedNode (show decompress option)
            if isinstance(self.node, CompressedNode):
                # Use plain text menu entries instead of emoji-prefixed labels
                decompress_action = menu.addAction("Decompress Node")
                decompress_action.setToolTip(
                    "Expand compressed node back to original nodes"
                )
            else:
                # Check if multiple nodes selected (show compress option)
                scene = self.scene()
                if scene:
                    selected = scene.selectedItems()
                    node_items = [
                        item for item in selected if isinstance(item, NodeItem)
                    ]
                    if len(node_items) >= 2:
                        compress_action = menu.addAction("Compress Selection")
                        compress_action.setToolTip(
                            "Combine selected sequential nodes into one"
                        )

            # Abstraction actions
            abstract_action = None
            expand_abstract_action = None

            # Check if this is an AbstractNode (show expand option)
            if isinstance(self.node, AbstractNode):
                expand_abstract_action = menu.addAction("🔷 Expand Abstract Node")
                expand_abstract_action.setToolTip(
                    "Expand abstract node back to original disjoint nodes"
                )
            else:
                # Check if multiple nodes selected (show abstract option)
                scene = self.scene()
                if scene:
                    selected = scene.selectedItems()
                    node_items = [
                        item for item in selected if isinstance(item, NodeItem)
                    ]
                    if len(node_items) >= 2:
                        abstract_action = menu.addAction("🔷 Abstract Selection")
                        abstract_action.setToolTip(
                            "Group selected disjoint nodes with same predecessors/successors"
                        )

            # === Multi-Graph Support: Sub-Graph Management ===
            create_subgraph_action = None
            add_to_subgraph_action = None
            remove_from_subgraph_menu = None
            rename_subgraph_action = None
            change_subgraph_color_action = None

            scene = self.scene()
            canvas = getattr(self, "canvas", None)
            graph = getattr(canvas, "graph", None) if canvas else None

            if scene and graph:
                selected = scene.selectedItems()
                node_items = [item for item in selected if isinstance(item, NodeItem)]
                if len(node_items) >= 1:
                    menu.addSeparator()
                    create_subgraph_action = menu.addAction(
                        "📦 Create Sub-Graph from Selection"
                    )
                    create_subgraph_action.setToolTip(
                        "Group selected nodes into a named sub-graph for separate processing"
                    )

                    # Add to existing sub-graph
                    existing_subgraphs = getattr(graph, "sub_graphs", [])
                    if existing_subgraphs:
                        add_to_subgraph_menu = menu.addMenu("➕ Add to Sub-Graph")
                        for sg in existing_subgraphs:
                            add_to_subgraph_menu.addAction(sg.graph_name)

                    # Remove from sub-graph (only if node is in any subgraph)
                    nodes = [item.node for item in node_items]
                    containing_subgraphs = []
                    for sg in existing_subgraphs:
                        if any(n in sg.nodes for n in nodes):
                            containing_subgraphs.append(sg)

                    if containing_subgraphs:
                        remove_from_subgraph_menu = menu.addMenu(
                            "➖ Remove from Sub-Graph"
                        )
                        for sg in containing_subgraphs:
                            remove_from_subgraph_menu.addAction(sg.graph_name)

                # Subgraph-specific options (rename, change color)
                # Check if right-clicked node is in exactly one subgraph
                if len(node_items) == 1:
                    node_subgraphs = graph.get_node_subgraphs(self.node)
                    if len(node_subgraphs) == 1:
                        sg = node_subgraphs[0]
                        menu.addSeparator()
                        rename_subgraph_action = menu.addAction(
                            f"✏️ Rename Sub-Graph '{sg.graph_name}'..."
                        )
                        change_subgraph_color_action = menu.addAction(
                            f"🎨 Change Sub-Graph Color..."
                        )

            menu.addSeparator()
            reset_node_action = menu.addAction("🔄 Reset Node")
            reinit_action = None
            if hasattr(self.node, "reinitialize"):
                reinit_action = menu.addAction("🎲 Reinitialize Weight")

            action = menu.exec(event.screenPos())

            if action == view_pred_action:
                try:
                    canvas = getattr(self, "canvas", None)
                    if canvas and hasattr(canvas, "graph") and canvas.graph:
                        from .predecessors_dialog import PredecessorsDialog

                        dlg = PredecessorsDialog(
                            self, canvas, parent=self.scene().views()[0].window()
                        )
                        dlg.exec()
                except Exception:
                    pass
            elif action == replace_action:
                try:
                    scene = self.scene()
                    if scene and scene.views():
                        view = scene.views()[0]
                        main_window = view.window()
                        if main_window and hasattr(main_window, "replace_node"):
                            main_window.replace_node(self)
                except Exception:
                    pass
            elif action == swallow_action:
                self._swallow_node()
            elif action == reset_node_action:
                self._reset_node()
            elif reinit_action and action == reinit_action:
                try:
                    self.node.reinitialize()
                    self.update_value_display()
                    self.update()
                except Exception:
                    pass
            elif compress_action and action == compress_action:
                self._compress_selection()
            elif decompress_action and action == decompress_action:
                self._decompress_node()
            elif abstract_action and action == abstract_action:
                self._abstract_selection()
            elif expand_abstract_action and action == expand_abstract_action:
                self._expand_abstract_node()
            elif create_subgraph_action and action == create_subgraph_action:
                self._create_subgraph_from_selection()
            # Handle Add to Sub-Graph submenu
            elif (
                add_to_subgraph_menu
                and action
                and action.parent() == add_to_subgraph_menu
            ):
                self._add_to_subgraph(action.text())
            # Handle Remove from Sub-Graph submenu
            elif (
                remove_from_subgraph_menu
                and action
                and action.parent() == remove_from_subgraph_menu
            ):
                self._remove_from_subgraph(action.text())
            elif rename_subgraph_action and action == rename_subgraph_action:
                self._rename_subgraph()
            elif (
                change_subgraph_color_action and action == change_subgraph_color_action
            ):
                self._change_subgraph_color()

        except Exception:
            pass

    def _swallow_node(self):
        """Swallow this node: remove it while connecting predecessors to successors."""
        try:
            canvas = getattr(self, "canvas", None)
            if canvas and hasattr(canvas, "swallow_selected_with_undo"):
                # Select this node if not already selected
                if not self.isSelected():
                    self.scene().clearSelection()
                    self.setSelected(True)
                canvas.swallow_selected_with_undo()
        except Exception:
            pass

    def _compress_selection(self):
        """Compress selected nodes into a CompressedNode."""
        try:
            canvas = getattr(self, "canvas", None)
            if canvas and hasattr(canvas, "compress_selected_with_undo"):
                canvas.compress_selected_with_undo()
        except Exception:
            pass

    def _decompress_node(self):
        """Decompress this CompressedNode back to original nodes."""
        try:
            canvas = getattr(self, "canvas", None)
            if canvas and hasattr(canvas, "decompress_node_with_undo"):
                canvas.decompress_node_with_undo(self, mode="full")
        except Exception:
            pass

    def _abstract_selection(self):
        """Abstract selected nodes into an AbstractNode."""
        try:
            canvas = getattr(self, "canvas", None)
            if canvas and hasattr(canvas, "abstract_selected_with_undo"):
                canvas.abstract_selected_with_undo()
        except Exception:
            pass

    def _expand_abstract_node(self):
        """Expand this AbstractNode back to original disjoint nodes."""
        try:
            canvas = getattr(self, "canvas", None)
            if canvas and hasattr(canvas, "expand_abstract_with_undo"):
                canvas.expand_abstract_with_undo(self)
        except Exception:
            pass

    def _reset_node(self):
        """Reset this node's value to its default state."""
        try:
            if hasattr(self.node, "ResetValue"):
                self.node.ResetValue()
                self.update_value_display()
                self.update()
        except Exception:
            pass

    def _create_subgraph_from_selection(self):
        """Create a sub-graph from the currently selected nodes."""
        try:
            from PyQt6.QtWidgets import QInputDialog, QMessageBox

            canvas = getattr(self, "canvas", None)
            if not canvas:
                return

            graph = getattr(canvas, "graph", None)
            if not graph:
                return

            # Get all selected nodes
            scene = self.scene()
            if not scene:
                return

            selected = scene.selectedItems()
            node_items = [item for item in selected if isinstance(item, NodeItem)]

            if not node_items:
                return

            # Get the actual node objects
            nodes = [item.node for item in node_items]

            # Prompt for sub-graph name
            name, ok = QInputDialog.getText(
                scene.views()[0] if scene.views() else None,
                "Create Sub-Graph",
                "Enter a name for the sub-graph:",
                text=f"Sub-Graph {len(getattr(graph, 'sub_graphs', [])) + 1}",
            )

            if not ok or not name.strip():
                return

            # Create the sub-graph
            try:
                subgraph = graph.create_subgraph_from_nodes(nodes, name.strip())
                if subgraph:
                    # Refresh the canvas to show the visual grouping
                    canvas.refresh_subgraph_visuals()

                    # Notify main window if available
                    if scene.views():
                        main_window = scene.views()[0].window()
                        if main_window and hasattr(main_window, "on_subgraph_created"):
                            main_window.on_subgraph_created(subgraph)

                    QMessageBox.information(
                        scene.views()[0] if scene.views() else None,
                        "Sub-Graph Created",
                        f"Sub-graph '{name}' created with {len(nodes)} nodes.",
                    )
            except ValueError as e:
                QMessageBox.warning(
                    scene.views()[0] if scene.views() else None,
                    "Cannot Create Sub-Graph",
                    str(e),
                )
        except Exception:
            pass

    def _add_to_subgraph(self, subgraph_name: str):
        """Add selected nodes to an existing sub-graph."""
        try:
            from PyQt6.QtWidgets import QMessageBox

            canvas = getattr(self, "canvas", None)
            if not canvas:
                return

            graph = getattr(canvas, "graph", None)
            if not graph:
                return

            # Find the subgraph
            subgraph = graph.find_subgraph_by_name(subgraph_name)
            if not subgraph:
                return

            # Get selected nodes
            scene = self.scene()
            if not scene:
                return

            selected = scene.selectedItems()
            nodes = [item.node for item in selected if isinstance(item, NodeItem)]

            if nodes:
                added = graph.add_nodes_to_subgraph(subgraph, nodes)
                if added > 0:
                    canvas.refresh_subgraph_visuals()
                    # Update graph selector
                    if scene.views():
                        main_window = scene.views()[0].window()
                        if main_window and hasattr(
                            main_window, "update_graph_selector"
                        ):
                            main_window.update_graph_selector()
        except Exception:
            pass

    def _remove_from_subgraph(self, subgraph_name: str):
        """Remove selected nodes from a sub-graph."""
        try:
            canvas = getattr(self, "canvas", None)
            if not canvas:
                return

            graph = getattr(canvas, "graph", None)
            if not graph:
                return

            # Find the subgraph
            subgraph = graph.find_subgraph_by_name(subgraph_name)
            if not subgraph:
                return

            # Get selected nodes
            scene = self.scene()
            if not scene:
                return

            selected = scene.selectedItems()
            nodes = [item.node for item in selected if isinstance(item, NodeItem)]

            if nodes:
                graph.remove_nodes_from_subgraph(subgraph, nodes)
                canvas.refresh_subgraph_visuals()
                # Update graph selector
                if scene.views():
                    main_window = scene.views()[0].window()
                    if main_window and hasattr(main_window, "update_graph_selector"):
                        main_window.update_graph_selector()
        except Exception:
            pass

    def _rename_subgraph(self):
        """Rename the sub-graph that this node belongs to."""
        try:
            from PyQt6.QtWidgets import QInputDialog

            canvas = getattr(self, "canvas", None)
            if not canvas:
                return

            graph = getattr(canvas, "graph", None)
            if not graph:
                return

            # Find subgraph containing this node
            subgraphs = graph.get_node_subgraphs(self.node)
            if not subgraphs:
                return

            subgraph = subgraphs[0]

            scene = self.scene()
            name, ok = QInputDialog.getText(
                scene.views()[0] if scene and scene.views() else None,
                "Rename Sub-Graph",
                "Enter new name:",
                text=subgraph.graph_name,
            )

            if ok and name.strip():
                graph.rename_subgraph(subgraph, name.strip())
                canvas.refresh_subgraph_visuals()
                # Update graph selector
                if scene and scene.views():
                    main_window = scene.views()[0].window()
                    if main_window and hasattr(main_window, "update_graph_selector"):
                        main_window.update_graph_selector()
        except Exception:
            pass

    def _change_subgraph_color(self):
        """Change the color of the sub-graph that this node belongs to."""
        try:
            from PyQt6.QtWidgets import QColorDialog

            canvas = getattr(self, "canvas", None)
            if not canvas:
                return

            graph = getattr(canvas, "graph", None)
            if not graph:
                return

            # Find subgraph containing this node
            subgraphs = graph.get_node_subgraphs(self.node)
            if not subgraphs:
                return

            subgraph = subgraphs[0]

            scene = self.scene()
            current_color = QColor(subgraph.graph_color)
            color = QColorDialog.getColor(
                current_color,
                scene.views()[0] if scene and scene.views() else None,
                f"Choose color for '{subgraph.graph_name}'",
            )

            if color.isValid():
                graph.set_subgraph_color(subgraph, color.name())
                canvas.refresh_subgraph_visuals()
                # Update graph selector
                if scene and scene.views():
                    main_window = scene.views()[0].window()
                    if main_window and hasattr(main_window, "update_graph_selector"):
                        main_window.update_graph_selector()
        except Exception:
            pass

    def paint(self, painter, option, widget):
        """Custom paint to show selection state and active nodes."""
        # Priority: Active > Selected > Manual Color > Value Color > Default
        if self.is_active:
            # Active nodes get the brightest color (thinking brain effect)
            self.setBrush(QBrush(self.active_color))
        elif self.isSelected():
            self.setBrush(QBrush(self.selected_color))
        else:
            manual_color = getattr(self, "manual_color", None)
            if manual_color is not None:
                # Manual color (from ANN colors or user) takes priority over value-based color
                self.setBrush(QBrush(manual_color))
            elif self.color is not None:
                # Use value-based color if set (from colorization)
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
            painter.drawEllipse(
                -self.radius, -self.radius, self.radius * 2, self.radius * 2
            )
        # Connection highlight applies to all selected nodes while connecting
        elif self.connection_highlight:
            painter.setPen(QPen(QColor(255, 215, 0), 3))  # Yellow-ish ring
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                -self.radius, -self.radius, self.radius * 2, self.radius * 2
            )

    def set_active(self, active):
        """Set whether this node is currently active (for Forward Processing)."""
        self.is_active = active
        self.update()  # Trigger repaint

    def _on_theme_changed(self):
        """Update default and text colors when the theme changes."""
        try:
            from .theme import get_theme_manager

            tm = get_theme_manager()
            # Only update default fill colors if this node uses the generic default
            from ComputationalGraphs.Nodes.AbstractNode import AbstractNode
            from ComputationalGraphs.Nodes.CompressedNode import CompressedNode

            if not isinstance(self.node, (AbstractNode, CompressedNode)):
                # Respect any user-applied default color override from the
                # visualization controller. Only update default colors from the
                # theme if the override is not present.
                if not getattr(self, "_default_color_overridden", False):
                    self.default_color = tm.get_color("node_default", "#003fbd")
                    self.selected_color = QColor(self.default_color).lighter(120)

            # Update text colors
            try:
                node_text = tm.get_color("node_text", "#ffffff")
                self.label.setDefaultTextColor(node_text)
                self.value_label.setDefaultTextColor(node_text)
            except Exception:
                pass
            try:
                muted = tm.get_color("muted_text", "#a0a0a0")
                self.topology_label.setDefaultTextColor(muted)
            except Exception:
                pass

            # Reapply node fonts from theme
            try:
                node_font = tm.get_font("node")
                node_font.setBold(True)
                self.label.setFont(node_font)
                value_font = tm.get_font("node")
                value_font.setPointSize(max(6, value_font.pointSize() - 2))
                self.value_label.setFont(value_font)
                topo_font = tm.get_font("node")
                topo_font.setPointSize(max(6, topo_font.pointSize() - 3))
                self.topology_label.setFont(topo_font)
            except Exception:
                pass

            self.update()
        except Exception:
            pass

    def set_manual_color(self, color):
        """Set a manual color for this node and update the display.

        Accepts QColor or None to clear the manual color. This centralizes
        mutating the manual_color attribute and ensures a consistent update.
        """
        try:
            self.manual_color = color
            self.update()
        except Exception:
            pass

    def clear_manual_color(self):
        """Clear the manual color and refresh the node visual."""
        try:
            self.manual_color = None
            self.update()
        except Exception:
            pass

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
                    if hasattr(view, "highlight_selected_nodes_for_connection"):
                        view.highlight_selected_nodes_for_connection(True)
        else:
            self.hover_edge = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            # Remove selected nodes highlight when not hovering
            if self.isSelected():
                scene = self.scene()
                if scene and scene.views():
                    view = scene.views()[0]
                    if hasattr(
                        view, "highlight_selected_nodes_for_connection"
                    ) and not getattr(view, "connection_mode", False):
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
            if hasattr(view, "highlight_selected_nodes_for_connection") and not getattr(
                view, "connection_mode", False
            ):
                view.highlight_selected_nodes_for_connection(False)
        self.update()
        super().hoverLeaveEvent(event)
