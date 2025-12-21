from typing import Optional

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class NewGraphViewModel(BaseViewModel):
    """ViewModel for creating a new computational graph."""

    properties_changed = ObservableProperty("properties_changed", default=0)

    def __init__(
        self,
        name: str = "NewGraph",
        num_inputs: int = 1,
        num_outputs: int = 1,
        graph_type: str = "MLP",
    ):
        super().__init__()
        self._name = name
        self._num_inputs = max(1, int(num_inputs))
        self._num_outputs = max(1, int(num_outputs))
        self._graph_type = graph_type
        self._created_graph = None

    def get_name(self) -> str:
        return self._name

    def set_name(self, name: str):
        if name != self._name:
            self._name = name
            self.properties_changed += 1

    def get_num_inputs(self) -> int:
        return self._num_inputs

    def set_num_inputs(self, n: int):
        n = max(1, int(n))
        if n != self._num_inputs:
            self._num_inputs = n
            self.properties_changed += 1

    def get_num_outputs(self) -> int:
        return self._num_outputs

    def set_num_outputs(self, n: int):
        n = max(1, int(n))
        if n != self._num_outputs:
            self._num_outputs = n
            self.properties_changed += 1

    def get_graph_type(self) -> str:
        return self._graph_type

    def set_graph_type(self, t: str):
        if t != self._graph_type:
            self._graph_type = t
            self.properties_changed += 1

    def create_graph(self):
        """Create a lightweight graph representation based on current settings.

        For now this returns a dict that can be used by higher-level code to
        construct a real graph object. Keeping it decoupled simplifies testing.
        """
        graph = {
            "name": self._name,
            "type": self._graph_type,
            "num_inputs": self._num_inputs,
            "num_outputs": self._num_outputs,
        }
        self._created_graph = graph
        return graph

    def get_created_graph(self):
        return self._created_graph

    # Lifecycle hooks
    def initialize(self) -> None:
        self._mark_initialized()

    def cleanup(self) -> None:
        pass
