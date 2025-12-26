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

    def generate(
        self,
        num_inputs: int,
        hidden_layers: List[int],
        num_outputs: int,
        activations=None,
        bias: bool = True,
        output_activation: str = None,
    ):
        """Return a simple mock graph (nodes with names and predecessors).

        activations: either a single activation name (str) or a list of names per hidden layer.
        bias: whether to include bias nodes flag on the returned graph (stored as attributes).
        output_activation: optional name of the activation for the output layer (e.g. 'Linear', 'Sigmoid').

        The returned graph object has attribute `nodes` containing nodes
        with `name` and `predecessors` attributes so it can be used by the
        CanvasViewModel or other components in tests and demos. Additionally it
        will include the following attributes for UI compatibility:
          - hiddenLayerSizes: List[int]
          - hiddenLayerActivations: List[str]
          - bias (bool)
        """

        class Node:
            def __init__(self, name):
                self.name = name
                self.predecessors = []
                # Compatibility with visualizer and graph runner which expect
                # nodes to have a 'value' attribute (and optional 'data').
                self.value = None
                self.data = None
                # Optional GUI attributes (position/color) may be set by file IO
                self.gui_pos = None
                self.gui_color = None
                self.gui_radius = None
                self.gui_label = None
                self.gui_label_color = None

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

        # Normalize activations: produce list of names matching hidden_layers length
        if activations is None:
            activations_list = ["Sigmoid"] * len(hidden_layers)
        elif isinstance(activations, str):
            activations_list = [activations] * len(hidden_layers)
        else:
            # assume iterable
            activations_list = list(activations)
            # pad/truncate to match hidden_layers
            if len(activations_list) < len(hidden_layers):
                activations_list = activations_list + [activations_list[-1]] * (
                    len(hidden_layers) - len(activations_list)
                )
            elif len(activations_list) > len(hidden_layers):
                activations_list = activations_list[: len(hidden_layers)]

        # Compatibility attributes used by older adapters/tests
        hiddenLayerSizes = list(hidden_layers)
        hiddenLayerActivations = list(activations_list)

        # Attempt to construct a real Core MLPGraph so weights/biases/buffers are generated
        try:
            from ComputationalGraphs.Core.MLPGraph import MLPGraph
            from ComputationalGraphs.Nodes.LinearNode import LinearNode
            from ComputationalGraphs.Nodes.ReLUNode import ReLUNode
            from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
            from ComputationalGraphs.Nodes.TanhNode import TanhNode

            # Map activation names to node classes
            activation_map = {
                "Sigmoid": SigmoidNode,
                "Tanh": TanhNode,
                "ReLU": ReLUNode,
                "Linear": LinearNode,
            }

            # Translate names to classes, default to SigmoidNode when unknown
            act_classes = []
            for name in hiddenLayerActivations:
                act_classes.append(activation_map.get(name, SigmoidNode))

            # Map output activation name to class (default to Linear)
            output_activation_map = {
                "Sigmoid": SigmoidNode,
                "Tanh": TanhNode,
                "ReLU": ReLUNode,
                "Linear": LinearNode,
            }
            output_cls = output_activation_map.get(output_activation, LinearNode)

            # Instantiate MLPGraph with provided settings (including output type)
            mlp = MLPGraph(
                numInputs=num_inputs,
                numOutputs=num_outputs,
                numHiddenLayers=len(hidden_layers),
                hiddenActivationFunctions=act_classes,
                hiddenLayerSizes=hiddenLayerSizes,
                add_bias=bool(bias),
                outputLayerType=output_cls,
            )
            mlp.BuildMLP()

            # Initialize node values to 0.0 where missing so visualizer doesn't show 'None'
            for node in getattr(mlp, "nodes", []):
                try:
                    if getattr(node, "value", None) is None:
                        node.value = 0.0
                except Exception:
                    pass

            # Attach compatibility attributes
            mlp.hiddenLayerActivations = hiddenLayerActivations
            mlp.hiddenLayerSizes = hiddenLayerSizes
            mlp.bias = bool(bias)
            mlp.hasBias = bool(bias)

            return mlp
        except Exception:
            # Fallback to a simple light-weight graph (legacy behavior)
            class Graph:
                def __init__(self, nodes):
                    self.nodes = nodes

            g = Graph(graph_nodes)
            g.hiddenLayerSizes = hiddenLayerSizes
            g.hiddenLayerActivations = hiddenLayerActivations
            g.bias = bool(bias)
            g.hasBias = bool(bias)

            # Try to convert to a Core.Graph if available so the returned object
            # integrates well with the rest of the application (AddNode API, ids, adjacency matrix)
            try:
                from ComputationalGraphs.Core.Graph import Graph as CoreGraph
                from ComputationalGraphs.Nodes.BasicNode import BasicNode

                class PlaceholderNode(BasicNode):
                    def __init__(self, name):
                        super().__init__(name)

                    def Operation(self, *inputs):
                        try:
                            return sum(inputs) if inputs else 0
                        except Exception:
                            return 0

                    def IsValidInput(self, inp):
                        return True

                core_g = CoreGraph(name=getattr(g, "graph_name", "Generated MLP"))

                old_to_new = {}
                for old_node in g.nodes:
                    new_node = PlaceholderNode(getattr(old_node, "name", ""))
                    # copy attributes
                    for attr in [
                        "value",
                        "data",
                        "gui_pos",
                        "gui_color",
                        "gui_radius",
                        "gui_label",
                        "gui_label_color",
                    ]:
                        try:
                            if hasattr(old_node, attr):
                                setattr(new_node, attr, getattr(old_node, attr))
                        except Exception:
                            pass
                    core_g.AddNode(new_node)
                    old_to_new[old_node] = new_node

                for old_node in g.nodes:
                    new_node = old_to_new.get(old_node)
                    preds = getattr(old_node, "predecessors", []) or []
                    for p in preds:
                        new_pred = old_to_new.get(p)
                        if new_pred is not None:
                            try:
                                core_g.ConnectPreNode(new_node, new_pred)
                            except Exception:
                                try:
                                    new_node.AddPreNode(new_pred)
                                except Exception:
                                    pass

                core_g.hiddenLayerSizes = g.hiddenLayerSizes
                core_g.hiddenLayerActivations = g.hiddenLayerActivations
                core_g.bias = g.bias
                core_g.hasBias = g.hasBias

                try:
                    core_g.UpdateAdjacencyMatrix()
                except Exception:
                    pass

                return core_g
            except Exception:
                # If Core.Graph not available, return light-weight graph for tests
                return g
