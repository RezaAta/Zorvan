"""
DeleteItemsCommand - Undoable command for deleting nodes and edges in MVVM canvas.

Integrates with CanvasViewModel to support undo/redo of deletions.
"""

try:
    from PyQt6.QtGui import QUndoCommand

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

    # Stub for testing without PyQt
    class QUndoCommand:
        def __init__(self, description=""):
            pass

        def redo(self):
            pass

        def undo(self):
            pass


if PYQT_AVAILABLE:
    from gui_framework.viewmodels.canvas_viewmodel import (
        EdgeRenderState,
        NodeRenderState,
    )

    class DeleteItemsCommand(QUndoCommand):
        """
        Command to delete nodes and edges from the canvas.

        Stores deleted items' state for restoration on undo and applies
        changes to the underlying graph model when available.
        """

        def __init__(
            self, viewmodel, node_ids, edge_ids=None, description="Delete Items"
        ):
            super().__init__(description)
            self.viewmodel = viewmodel
            self.node_ids = list(node_ids)
            self.edge_ids = list(edge_ids) if edge_ids else []

            # Collected state for undo/redo
            self.deleted_nodes = []  # list of dicts {id, node_obj, x, y}
            self.deleted_edges = (
                []
            )  # list of dicts {edge_id, src_name, tgt_name, src_obj, tgt_obj}

            # Resolve and capture state from viewmodel/graph
            for nid in self.node_ids:
                node_state = None
                try:
                    node_state = self.viewmodel.get_node(nid)
                except Exception:
                    node_state = None

                x = getattr(node_state, "x", 0)
                y = getattr(node_state, "y", 0)

                node_obj = None
                try:
                    if (
                        hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        for n in self.viewmodel._graph.nodes:
                            if (
                                getattr(n, "name", None) == nid
                                or getattr(n, "id", None) == nid
                            ):
                                node_obj = n
                                break
                except Exception:
                    node_obj = None

                self.deleted_nodes.append(
                    {"id": nid, "node_obj": node_obj, "x": x, "y": y}
                )

            for eid in self.edge_ids:
                edge_state = None
                try:
                    edge_state = self.viewmodel.get_edge(eid)
                except Exception:
                    edge_state = None

                src_name = getattr(edge_state, "source_node_id", None)
                tgt_name = getattr(edge_state, "target_node_id", None)

                src_obj = tgt_obj = None
                try:
                    if (
                        hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        for n in self.viewmodel._graph.nodes:
                            if (
                                getattr(n, "name", None) == src_name
                                or getattr(n, "id", None) == src_name
                            ):
                                src_obj = n
                                break
                        for n in self.viewmodel._graph.nodes:
                            if (
                                getattr(n, "name", None) == tgt_name
                                or getattr(n, "id", None) == tgt_name
                            ):
                                tgt_obj = n
                                break
                except Exception:
                    src_obj = tgt_obj = None

                self.deleted_edges.append(
                    {
                        "edge_id": eid,
                        "src_name": src_name,
                        "tgt_name": tgt_name,
                        "src_obj": src_obj,
                        "tgt_obj": tgt_obj,
                    }
                )

        def redo(self):
            """Apply deletions to viewmodel and underlying graph where possible."""
            # Remove edges first
            for e in self.deleted_edges:
                eid = e.get("edge_id")
                src_obj = e.get("src_obj")
                tgt_obj = e.get("tgt_obj")

                # Remove render edge if exists
                try:
                    if eid in getattr(self.viewmodel, "_edges", {}):
                        del self.viewmodel._edges[eid]
                        self.viewmodel.edges_changed += 1
                except Exception:
                    pass

                # Disconnect in graph if possible
                try:
                    if (
                        src_obj is not None
                        and tgt_obj is not None
                        and hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        if hasattr(self.viewmodel._graph, "DisconnectPreNode"):
                            try:
                                self.viewmodel._graph.DisconnectPreNode(
                                    tgt_obj, src_obj
                                )
                            except Exception:
                                # Fallback to manual predecessor removal
                                try:
                                    if hasattr(tgt_obj, "predecessors"):
                                        for p in list(tgt_obj.predecessors):
                                            if getattr(p, "name", None) == getattr(
                                                src_obj, "name", None
                                            ) or getattr(p, "id", None) == getattr(
                                                src_obj, "id", None
                                            ):
                                                try:
                                                    tgt_obj.predecessors.remove(p)
                                                except Exception:
                                                    pass
                                except Exception:
                                    pass
                        else:
                            # Simple graph-like object: manipulate predecessors if available
                            try:
                                if hasattr(tgt_obj, "predecessors"):
                                    for p in list(tgt_obj.predecessors):
                                        if getattr(p, "name", None) == getattr(
                                            src_obj, "name", None
                                        ) or getattr(p, "id", None) == getattr(
                                            src_obj, "id", None
                                        ):
                                            try:
                                                tgt_obj.predecessors.remove(p)
                                            except Exception:
                                                pass
                            except Exception:
                                pass
                except Exception:
                    pass

            # Remove nodes
            for n in self.deleted_nodes:
                nid = n.get("id")
                node_obj = n.get("node_obj")

                # Remove from viewmodel render state
                try:
                    if nid in getattr(self.viewmodel, "_nodes", {}):
                        del self.viewmodel._nodes[nid]
                        self.viewmodel.nodes_changed += 1
                except Exception:
                    pass

                # Remove from graph
                try:
                    if (
                        node_obj is not None
                        and hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        # Prefer Graph.RemoveNode if available
                        if hasattr(self.viewmodel._graph, "RemoveNode"):
                            try:
                                self.viewmodel._graph.RemoveNode(node_obj)
                            except Exception:
                                # Fallback to manual removal
                                try:
                                    if node_obj in self.viewmodel._graph.nodes:
                                        self.viewmodel._graph.nodes.remove(node_obj)
                                except Exception:
                                    pass
                        else:
                            # Simple graph-like object: remove by name/id
                            try:
                                to_remove = None
                                for n in list(self.viewmodel._graph.nodes):
                                    if (
                                        getattr(n, "name", None) == nid
                                        or getattr(n, "id", None) == nid
                                    ):
                                        to_remove = n
                                        break
                                if to_remove is not None:
                                    self.viewmodel._graph.nodes.remove(to_remove)
                            except Exception:
                                pass
                except Exception:
                    pass

        def undo(self):
            """Restore deleted nodes and edges to viewmodel and graph."""
            # Restore nodes first
            from gui_framework.viewmodels.canvas_viewmodel import (
                EdgeRenderState,
                NodeRenderState,
            )

            for n in self.deleted_nodes:
                nid = n.get("id")
                node_obj = n.get("node_obj")
                x = n.get("x", 0)
                y = n.get("y", 0)

                # Add back to graph (support both rich Graph API and simple list-like Graph)
                try:
                    if (
                        node_obj is not None
                        and hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        if hasattr(self.viewmodel._graph, "AddNode"):
                            try:
                                if node_obj not in self.viewmodel._graph.nodes:
                                    self.viewmodel._graph.AddNode(node_obj)
                            except Exception:
                                # Fallback to simple append
                                try:
                                    if node_obj not in self.viewmodel._graph.nodes:
                                        self.viewmodel._graph.nodes.append(node_obj)
                                except Exception:
                                    pass
                        else:
                            try:
                                if node_obj not in self.viewmodel._graph.nodes:
                                    self.viewmodel._graph.nodes.append(node_obj)
                            except Exception:
                                pass
                except Exception:
                    pass

                # Restore render state
                try:
                    if nid not in getattr(self.viewmodel, "_nodes", {}):
                        node_state = NodeRenderState(node_id=nid, name=nid, x=x, y=y)
                        self.viewmodel._nodes[nid] = node_state
                        self.viewmodel.nodes_changed += 1
                except Exception:
                    pass

            # Restore edges
            for e in self.deleted_edges:
                eid = e.get("edge_id")
                src_obj = e.get("src_obj")
                tgt_obj = e.get("tgt_obj")
                src_name = e.get("src_name")
                tgt_name = e.get("tgt_name")

                # Reconnect in graph
                try:
                    if (
                        src_obj is not None
                        and tgt_obj is not None
                        and hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        if hasattr(self.viewmodel._graph, "ConnectPreNode"):
                            try:
                                self.viewmodel._graph.ConnectPreNode(tgt_obj, src_obj)
                            except Exception:
                                # Fallback to direct predecessor append
                                try:
                                    if (
                                        hasattr(tgt_obj, "predecessors")
                                        and src_obj not in tgt_obj.predecessors
                                    ):
                                        tgt_obj.predecessors.append(src_obj)
                                except Exception:
                                    pass
                        else:
                            try:
                                if (
                                    hasattr(tgt_obj, "predecessors")
                                    and src_obj not in tgt_obj.predecessors
                                ):
                                    tgt_obj.predecessors.append(src_obj)
                            except Exception:
                                pass
                except Exception:
                    pass

                # Restore render edge
                try:
                    if eid not in getattr(self.viewmodel, "_edges", {}):
                        edge_state = EdgeRenderState(
                            edge_id=eid,
                            source_node_id=src_name,
                            target_node_id=tgt_name,
                        )
                        self.viewmodel._edges[eid] = edge_state
                        self.viewmodel.edges_changed += 1
                except Exception:
                    pass

else:
    # Non-Qt stub that performs the same model operations so unit tests can run
    class DeleteItemsCommand:
        def __init__(
            self, viewmodel, node_ids, edge_ids=None, description="Delete Items"
        ):
            self.viewmodel = viewmodel
            self.node_ids = list(node_ids)
            self.edge_ids = list(edge_ids) if edge_ids else []

            self.deleted_nodes = []
            self.deleted_edges = []

            for nid in self.node_ids:
                node_state = None
                try:
                    node_state = self.viewmodel.get_node(nid)
                except Exception:
                    node_state = None

                x = getattr(node_state, "x", 0)
                y = getattr(node_state, "y", 0)

                node_obj = None
                try:
                    if (
                        hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        for n in self.viewmodel._graph.nodes:
                            if (
                                getattr(n, "name", None) == nid
                                or getattr(n, "id", None) == nid
                            ):
                                node_obj = n
                                break
                except Exception:
                    node_obj = None

                self.deleted_nodes.append(
                    {"id": nid, "node_obj": node_obj, "x": x, "y": y}
                )

            for eid in self.edge_ids:
                edge_state = None
                try:
                    edge_state = self.viewmodel.get_edge(eid)
                except Exception:
                    edge_state = None

                src_name = getattr(edge_state, "source_node_id", None)
                tgt_name = getattr(edge_state, "target_node_id", None)

                src_obj = tgt_obj = None
                try:
                    if (
                        hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        for n in self.viewmodel._graph.nodes:
                            if (
                                getattr(n, "name", None) == src_name
                                or getattr(n, "id", None) == src_name
                            ):
                                src_obj = n
                                break
                        for n in self.viewmodel._graph.nodes:
                            if (
                                getattr(n, "name", None) == tgt_name
                                or getattr(n, "id", None) == tgt_name
                            ):
                                tgt_obj = n
                                break
                except Exception:
                    src_obj = tgt_obj = None

                self.deleted_edges.append(
                    {
                        "edge_id": eid,
                        "src_name": src_name,
                        "tgt_name": tgt_name,
                        "src_obj": src_obj,
                        "tgt_obj": tgt_obj,
                    }
                )

        def redo(self):
            # Remove edges first
            for e in self.deleted_edges:
                eid = e.get("edge_id")
                src_obj = e.get("src_obj")
                tgt_obj = e.get("tgt_obj")

                try:
                    if eid in getattr(self.viewmodel, "_edges", {}):
                        del self.viewmodel._edges[eid]
                        self.viewmodel.edges_changed += 1
                except Exception:
                    pass

                try:
                    if (
                        src_obj is not None
                        and tgt_obj is not None
                        and hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        self.viewmodel._graph.DisconnectPreNode(tgt_obj, src_obj)
                except Exception:
                    pass

            # Remove nodes
            for n in self.deleted_nodes:
                nid = n.get("id")
                node_obj = n.get("node_obj")

                try:
                    if nid in getattr(self.viewmodel, "_nodes", {}):
                        del self.viewmodel._nodes[nid]
                        self.viewmodel.nodes_changed += 1
                except Exception:
                    pass

                try:
                    if (
                        node_obj is not None
                        and hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        if node_obj in self.viewmodel._graph.nodes:
                            self.viewmodel._graph.RemoveNode(node_obj)
                except Exception:
                    pass

        def undo(self):
            from gui_framework.viewmodels.canvas_viewmodel import (
                EdgeRenderState,
                NodeRenderState,
            )

            for n in self.deleted_nodes:
                nid = n.get("id")
                node_obj = n.get("node_obj")
                x = n.get("x", 0)
                y = n.get("y", 0)

                try:
                    if (
                        node_obj is not None
                        and hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        if node_obj not in self.viewmodel._graph.nodes:
                            self.viewmodel._graph.AddNode(node_obj)
                except Exception:
                    pass

                try:
                    if nid not in getattr(self.viewmodel, "_nodes", {}):
                        node_state = NodeRenderState(node_id=nid, name=nid, x=x, y=y)
                        self.viewmodel._nodes[nid] = node_state
                        self.viewmodel.nodes_changed += 1
                except Exception:
                    pass

            for e in self.deleted_edges:
                eid = e.get("edge_id")
                src_obj = e.get("src_obj")
                tgt_obj = e.get("tgt_obj")
                src_name = e.get("src_name")
                tgt_name = e.get("tgt_name")

                try:
                    if (
                        src_obj is not None
                        and tgt_obj is not None
                        and hasattr(self.viewmodel, "_graph")
                        and self.viewmodel._graph is not None
                    ):
                        self.viewmodel._graph.ConnectPreNode(tgt_obj, src_obj)
                except Exception:
                    pass

                try:
                    if eid not in getattr(self.viewmodel, "_edges", {}):
                        edge_state = EdgeRenderState(
                            edge_id=eid,
                            source_node_id=src_name,
                            target_node_id=tgt_name,
                        )
                        self.viewmodel._edges[eid] = edge_state
                        self.viewmodel.edges_changed += 1
                except Exception:
                    pass
