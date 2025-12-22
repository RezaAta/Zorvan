"""BackpropViewModel - Manages adding/removing BackpropGraph to MLP graphs."""

from typing import Optional

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty

try:
    from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
    from ComputationalGraphs.Core.Graph import Graph
    from ComputationalGraphs.Core.MLPGraph import MLPGraph

    BACKPROP_AVAILABLE = True
except Exception:
    BACKPROP_AVAILABLE = False


class BackpropViewModel(BaseViewModel):
    """ViewModel for the Backprop dialog.

    Responsibilities:
    - Hold reference to current graph
    - Expose learning rate as observable property
    - Add/Remove backprop and expose generated graph
    """

    learning_rate = ObservableProperty("learning_rate", default=0.01)
    generated_graph_changed = ObservableProperty("generated_graph_changed", default=0)

    def __init__(self, current_graph=None):
        super().__init__()
        self.current_graph = current_graph
        self._generated_graph: Optional["Graph"] = None

    def initialize(self):
        # lifecycle stub
        return True

    def cleanup(self):
        # lifecycle stub
        return True

    def set_learning_rate(self, lr: float):
        self.learning_rate = float(lr)

    def get_learning_rate(self) -> float:
        return float(self.learning_rate)

    def add_backprop(self) -> bool:
        if not BACKPROP_AVAILABLE:
            return False
        try:
            if not isinstance(self.current_graph, MLPGraph):
                # Still attempt; BackpropGraph may accept the graph type
                pass

            backprop_graph = BackpropGraph(
                self.current_graph, learningRate=self.get_learning_rate()
            )
            backprop_graph.BuildBackprop()

            full_graph = Graph()
            for node in getattr(self.current_graph, "nodes", []):
                full_graph.AddNode(node)
            for node in getattr(backprop_graph, "nodes", []):
                full_graph.AddNode(node)
            full_graph.UpdateAdjacencyMatrix()

            self._generated_graph = full_graph
            self.generated_graph_changed += 1
            return True
        except Exception:
            return False

    def remove_backprop(self) -> bool:
        if not BACKPROP_AVAILABLE:
            return False
        try:
            BackpropGraph.RemoveBackpropFromGraph(self.current_graph)
            self._generated_graph = self.current_graph
            self.generated_graph_changed += 1
            return True
        except Exception:
            return False

    def get_generated_graph(self):
        return self._generated_graph
