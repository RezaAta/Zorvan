"""PredecessorsViewModel - provides list of predecessors and disconnect logic."""

from typing import List, Optional

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class PredecessorsViewModel(BaseViewModel):
    """ViewModel exposing predecessors of a node and allowing disconnects."""

    list_changed = ObservableProperty("list_changed", default=0)

    def __init__(self, node_item=None, canvas=None):
        super().__init__()
        self.node_item = node_item
        self.canvas = canvas
        self.graph = getattr(canvas, "graph", None) if canvas is not None else None
        self._predecessors: List[object] = []

    def initialize(self) -> None:
        """Lifecycle initialize called by views."""
        self._mark_initialized()

    def cleanup(self) -> None:
        """Cleanup resources (no-op)."""
        pass

    def load(self, node_item, canvas):
        self.node_item = node_item
        self.canvas = canvas
        self.graph = getattr(canvas, "graph", None) if canvas is not None else None
        self.refresh()

    def get_predecessors(self) -> List[object]:
        return list(self._predecessors)

    def refresh(self):
        preds_by_obj = set()
        try:
            # Try to resolve authoritative graph node
            graph_node = None
            if self.graph is not None:
                node_id = getattr(self.node_item.node, "id", None)
                node_name = getattr(self.node_item.node, "name", None)
                if node_id and node_id in self.graph.idToNodeDictionary:
                    graph_node = self.graph.idToNodeDictionary[node_id]
                else:
                    for gn in self.graph.nodes:
                        if getattr(gn, "name", None) == node_name:
                            graph_node = gn
                            break
            if graph_node is not None:
                preds_by_obj.update(graph_node.predecessors)
            else:
                if hasattr(self.node_item.node, "predecessors"):
                    preds_by_obj.update(self.node_item.node.predecessors)
        except Exception:
            preds_by_obj = set()

        # Also include visual edges from canvas
        try:
            for edge in getattr(self.canvas, "edge_items", []):
                if edge.target_node == self.node_item:
                    preds_by_obj.add(edge.source_node.node)
        except Exception:
            pass

        self._predecessors = list(preds_by_obj)
        self.list_changed += 1

    def disconnect(self, pred_node) -> bool:
        """Disconnect the given predecessor node from the current node.

        Returns True if disconnect seems successful (no exception).
        """
        try:
            # Determine authoritative graph node like in refresh
            graph_node = None
            try:
                if self.graph is not None:
                    node_id = getattr(self.node_item.node, "id", None)
                    node_name = getattr(self.node_item.node, "name", None)
                    if node_id and node_id in self.graph.idToNodeDictionary:
                        graph_node = self.graph.idToNodeDictionary[node_id]
                    else:
                        for gn in self.graph.nodes:
                            if getattr(gn, "name", None) == node_name:
                                graph_node = gn
                                break
            except Exception:
                graph_node = None

            pred_to_remove = pred_node
            if graph_node is not None:
                for p in list(graph_node.predecessors):
                    if p is pred_node or getattr(p, "name", None) == getattr(
                        pred_node, "name", None
                    ):
                        pred_to_remove = p
                        break

            if self.graph is not None:
                try:
                    self.graph.DisconnectPreNode(
                        graph_node or self.node_item.node, pred_to_remove
                    )
                except Exception:
                    pass

            # Remove visual edges from canvas
            try:
                for edge in list(getattr(self.canvas, "edge_items", [])):
                    src_node = edge.source_node.node
                    tgt_node = edge.target_node.node
                    match_src = False
                    if src_node is pred_node or getattr(
                        src_node, "name", None
                    ) == getattr(pred_node, "name", None):
                        match_src = True
                    if match_src and tgt_node is self.node_item.node:
                        try:
                            # emit signal if exists
                            try:
                                self.canvas.edge_removed.emit(
                                    pred_node, self.node_item.node
                                )
                            except Exception:
                                pass
                            edge.remove()
                            try:
                                if edge in self.canvas.edge_items:
                                    self.canvas.edge_items.remove(edge)
                            except Exception:
                                pass
                        except Exception:
                            pass
            except Exception:
                pass

            self.refresh()
            return True
        except Exception:
            return False
