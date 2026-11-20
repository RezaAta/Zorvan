from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import GraphCanvas


def _build_concurrent_mlp_with_bias():
    """Concurrent 2-input MLP (2 hidden ReLU layers, bias on) with backprop and MSE nodes."""
    from zorvan_reference.Core.BackpropGraph import BackpropGraph
    from zorvan_reference.Core.Graph import Graph
    from zorvan_reference.Core.MLPGraph import MLPGraph
    from zorvan_reference.Nodes.LinearNode import LinearNode
    from zorvan_reference.Nodes.ReLUNode import ReLUNode

    X = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]
    y = [[0.0, 1.0, 1.0, 0.0]]
    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=2,
        hiddenLayerSizes=[3, 4],
        activationFunction=ReLUNode,
        outputLayerType=LinearNode,
        add_bias=True,
    )
    mlp.BuildMLP()
    mlp.LoadData(X, y)
    backprop = BackpropGraph(mlp, learningRate=0.01)
    backprop.BuildBackprop()
    mlp.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X[0]))

    g = Graph()
    for n in list(mlp.nodes) + list(backprop.nodes) + mlp.errorBuffers + mlp.mseNodes:
        if n not in g.nodes:
            g.AddNode(n)
    g.UpdateAdjacencyMatrix()
    return g


def test_bias_and_ms_colors():
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication([])
        owns_app = True
    g = _build_concurrent_mlp_with_bias()
    canvas = GraphCanvas(None)
    canvas.graph = g
    for idx, n in enumerate(g.nodes):
        canvas.add_node_item(n, idx * 10, idx * 10)

    # Ensure canvas not in ANN colors initially
    assert canvas.ann_colors_active is False

    canvas.apply_ann_colors()
    # After applying colors, check at least one bias node and one MS node
    bias_items = [
        item
        for node, item in canvas.node_items.items()
        if getattr(node, "name", "").startswith("B_")
    ]
    ms_items = [
        item
        for node, item in canvas.node_items.items()
        if getattr(node, "name", "").startswith("MS_")
        or getattr(node, "name", "").startswith("MSE_")
    ]
    assert bias_items, "No bias items found in canvas for checking colors."
    # Check at least one bias item is colored blue (weights are blue = (60,100,180))
    blue_color = QColor(60, 100, 180)
    found_blue = any(
        getattr(item, "manual_color", None) == blue_color for item in bias_items
    )
    assert found_blue, "No bias nodes found with blue ANN color."

    # Check MS nodes are red if present
    if ms_items:
        red_color = QColor(180, 60, 60)
        found_red = any(
            getattr(item, "manual_color", None) == red_color for item in ms_items
        )
        assert found_red, "No MS nodes found with red ANN color."
    if owns_app:
        app.quit()
