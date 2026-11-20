# Adapter for MVVM PredecessorsDialog (delegates to gui_framework implementation)
try:
    from gui_framework.viewmodels.dialogs.predecessors_viewmodel import (
        PredecessorsViewModel,
    )
    from gui_framework.views.dialogs.predecessors_dialog import (
        PredecessorsDialog as MVVMPredecessorsDialog,
    )
except Exception:
    MVVMPredecessorsDialog = None


class PredecessorsDialog:
    """Legacy import adapter that delegates to MVVM-based dialog when available."""

    def __init__(self, node_item, canvas, parent=None):
        if MVVMPredecessorsDialog is None:
            raise ImportError("Predecessors MVVM components not available")
        # Keep references locally so legacy adapter methods can access them
        self.node_item = node_item
        self.canvas = canvas
        self.graph = getattr(canvas, "graph", None)
        # Connect to canvas signals so the dialog updates when edges are created/removed
        try:
            if hasattr(self.canvas, "edge_removed"):
                try:
                    self.canvas.edge_removed.connect(self._on_canvas_edge_changed)
                except Exception:
                    pass
            if hasattr(self.canvas, "edge_created"):
                try:
                    self.canvas.edge_created.connect(self._on_canvas_edge_changed)
                except Exception:
                    pass
        except Exception:
            pass
        vm = PredecessorsViewModel(node_item=node_item, canvas=canvas)
        vm.initialize()
        self._dlg = MVVMPredecessorsDialog(vm, parent)

    def exec(self):
        return self._dlg.exec()

    def close(self):
        return self._dlg.close()

    def __getattr__(self, name):
        return getattr(self._dlg, name)

    def populate(self):
        self.list_widget.clear()
        # Resolve the authoritative node instance from the graph (by name/id), if available.
        graph_node = None
        try:
            if hasattr(self.canvas, "graph") and self.canvas.graph is not None:
                # Prefer id match then name match
                node_id = getattr(self.node_item.node, "id", None)
                node_name = getattr(self.node_item.node, "name", None)
                if node_id and node_id in self.canvas.graph.idToNodeDictionary:
                    graph_node = self.canvas.graph.idToNodeDictionary[node_id]
                else:
                    # fallback: find by name
                    for gn in self.canvas.graph.nodes:
                        if getattr(gn, "name", None) == node_name:
                            graph_node = gn
                            break
        except Exception:
            graph_node = None

        # Start with graph predecessors (if available); else fallback to the NodeItem node object
        if graph_node is not None:
            preds_by_obj = set(graph_node.predecessors)
        else:
            preds_by_obj = (
                set(self.node_item.node.predecessors)
                if hasattr(self.node_item.node, "predecessors")
                else set()
            )
        # Also check canvas edge items in case visual edges exist but graph hasn't been updated
        try:
            for edge in self.canvas.edge_items:
                if edge.target_node == self.node_item:
                    preds_by_obj.add(edge.source_node.node)
        except Exception:
            pass
        preds = list(preds_by_obj)
        for p in preds:
            # Create a composite widget to show an 'X' disconnect button and the predecessor node name
            row_widget = QWidget()
            # help avoid cramped rows on high-DPI or small font setups
            row_widget.setMinimumHeight(40)
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(6, 4, 6, 4)
            row_layout.setSpacing(8)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            # Small tool button with X icon
            try:
                from PyQt6.QtWidgets import QToolButton

                btn = QToolButton()
                try:
                    btn.setProperty("themed", True)
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn.setMouseTracking(True)
                except Exception:
                    pass
                # Use plain ASCII 'X' to avoid emoji characters in UI
                btn.setText("X")
                btn.setFixedSize(26, 26)
                btn.setToolTip("Disconnect predecessor")
                btn.setStyleSheet("font-size: 12px; padding: 0px;")
            except Exception:
                btn = QPushButton("X")
                btn.setFixedSize(28, 28)
                btn.setStyleSheet("font-size: 12px; padding: 0px;")
            label = QLabel(p.name if hasattr(p, "name") else str(p))
            label.setStyleSheet("padding-left: 6px")
            # Expand label to use remaining width
            label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            # Clear elide by allowing word wrap if too long
            label.setWordWrap(False)
            # Slightly larger font for readability
            try:
                from PyQt6.QtGui import QFont

                f = label.font()
                f.setPointSize(max(9, f.pointSize()))
                label.setFont(f)
            except Exception:
                pass

            # Connect button to disconnect handler
            btn.clicked.connect(lambda _, pred=p: self.disconnect_pred(pred))

            row_layout.addWidget(btn)
            row_layout.addWidget(label)
            row_layout.addStretch(1)
            row_widget.setLayout(row_layout)

            list_item = QListWidgetItem()
            from PyQt6.QtCore import QSize

            min_size = QSize(320, 44)
            size_hint = row_widget.sizeHint().expandedTo(min_size)
            list_item.setSizeHint(size_hint)
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, row_widget)

    def disconnect_pred(self, pred_node):
        # Disconnect from underlying graph
        try:
            if self.graph is not None:
                # Determine authoritative graph node object
                graph_node = None
                try:
                    node_id = getattr(self.node_item.node, "id", None)
                    node_name = getattr(self.node_item.node, "name", None)
                    if node_id and node_id in self.canvas.graph.idToNodeDictionary:
                        graph_node = self.canvas.graph.idToNodeDictionary[node_id]
                    else:
                        for gn in self.canvas.graph.nodes:
                            if getattr(gn, "name", None) == node_name:
                                graph_node = gn
                                break
                except Exception:
                    graph_node = None

                # Determine predecessor to pass to disconnect - prefer graph's predecessor instances
                pred_to_remove = pred_node
                if graph_node is not None:
                    # Match by name or id if pred_node is not the same object
                    for p in list(graph_node.predecessors):
                        if p is pred_node:
                            pred_to_remove = p
                            break
                        if getattr(p, "name", None) == getattr(pred_node, "name", None):
                            pred_to_remove = p
                            break

                try:
                    self.graph.DisconnectPreNode(
                        graph_node or self.node_item.node, pred_to_remove
                    )
                except Exception:
                    pass
            # Also remove visual edges from canvas
            try:
                # remove all visual edge items that connect pred_node->node
                for edge in list(self.canvas.edge_items):
                    # Compare by resolved predecessor object in graph (match by name/id if necessary)
                    src_node = edge.source_node.node
                    tgt_node = edge.target_node.node
                    match_src = False
                    if src_node is pred_node:
                        match_src = True
                    else:
                        # try by name
                        try:
                            if getattr(src_node, "name", None) == getattr(
                                pred_node, "name", None
                            ):
                                match_src = True
                        except Exception:
                            pass
                    if match_src and tgt_node is self.node_item.node:
                        try:
                            self.canvas.edge_removed.emit(
                                pred_node, self.node_item.node
                            )
                        except Exception:
                            pass
                        edge.remove()
                        if edge in self.canvas.edge_items:
                            try:
                                self.canvas.edge_items.remove(edge)
                            except Exception:
                                pass
            except Exception:
                pass
        finally:
            self.populate()

    def _on_canvas_edge_changed(self, src, tgt):
        # If this dialog shows the predecessors of a node that changed, refresh
        try:
            if src == self.node_item.node or tgt == self.node_item.node:
                self.populate()
        except Exception:
            pass

    def closeEvent(self, event):
        # Detach canvas signals to avoid memory leaks
        try:
            if hasattr(self.canvas, "edge_removed"):
                try:
                    self.canvas.edge_removed.disconnect(self._on_canvas_edge_changed)
                except Exception:
                    pass
            if hasattr(self.canvas, "edge_created"):
                try:
                    self.canvas.edge_created.disconnect(self._on_canvas_edge_changed)
                except Exception:
                    pass
        except Exception:
            pass
        super().closeEvent(event)
