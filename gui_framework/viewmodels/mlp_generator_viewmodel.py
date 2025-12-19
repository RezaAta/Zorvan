"""
MLP Generator ViewModel: small helper to create a simple MLP-like graph
structure for examples and testing.
"""

from typing import List

from gui_framework.viewmodels.base import BaseViewModel


class MLPGeneratorViewModel(BaseViewModel):
    def __init__(self):
        super().__init__()

    def initialize(self):
        self._mark_initialized()

    def cleanup(self):
        pass

    def generate(self, num_inputs: int, hidden_layers: List[int], num_outputs: int):
        """Return a simple mock graph (nodes with names and predecessors).

        The returned graph object has attribute `nodes` containing nodes
        with `name` and `predecessors` attributes so it can be used by the
        CanvasViewModel or other components in tests and demos.
        """

        class Node:
            def __init__(self, name):
                self.name = name
                self.predecessors = []

        graph_nodes = []

        # Input nodes
        input_nodes = [Node(f"x{i}") for i in range(num_inputs)]
        graph_nodes.extend(input_nodes)

        prev_layer = input_nodes
        # Hidden layers
        for layer_idx, size in enumerate(hidden_layers):
            layer_nodes = [Node(f"H{layer_idx}N{j}") for j in range(size)]
            for ln in layer_nodes:
                ln.predecessors = list(prev_layer)
            graph_nodes.extend(layer_nodes)
            prev_layer = layer_nodes

        # Output layer
        output_nodes = [Node(f"y{j}") for j in range(num_outputs)]
        for out in output_nodes:
            out.predecessors = list(prev_layer)
        graph_nodes.extend(output_nodes)

        # Create simple graph container
        class Graph:
            def __init__(self, nodes):
                self.nodes = nodes

        return Graph(graph_nodes)
