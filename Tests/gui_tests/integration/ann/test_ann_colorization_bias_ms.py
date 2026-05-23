from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from zorvan.GUI.examples_loader import ExamplesLoader
from zorvan.GUI.graph_canvas import GraphCanvas


def test_bias_and_ms_colors():
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication([])
        owns_app = True
    loader = ExamplesLoader()
    g = loader._build_piecewise_mlp2_concurrent()
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
