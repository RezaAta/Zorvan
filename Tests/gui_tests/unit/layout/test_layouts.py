import math

from gui_framework.layouts import apply_layout


class SimpleNode:
    def __init__(self, name, preds=None):
        self.name = name
        self.predecessors = preds or []


def get_preds(node):
    return node.predecessors


def test_apply_grid_layout_returns_positions():
    nodes = [SimpleNode(f"n{i}") for i in range(9)]
    pos = apply_layout(nodes, get_preds, algorithm="grid", cols=3, spacing=50)

    assert isinstance(pos, dict)
    assert len(pos) == 9
    # Each node should have numeric coordinates
    for k, v in pos.items():
        assert isinstance(k, str)
        assert isinstance(v, tuple)
        assert isinstance(v[0], float) or isinstance(v[0], int)


def test_apply_circular_layout_positions_on_circle():
    nodes = [SimpleNode(f"n{i}") for i in range(8)]
    pos = apply_layout(nodes, get_preds, algorithm="circular", radius=200)

    # Check that each position lies approximately at radius
    for x, y in pos.values():
        r = math.hypot(x, y)
        assert 180 <= r <= 220


def test_apply_layout_with_predecessors_nonempty():
    # Create a little chain A -> B -> C to ensure functions that rely on predecessors handle it
    a = SimpleNode("A")
    b = SimpleNode("B", preds=[a])
    c = SimpleNode("C", preds=[b])
    nodes = [a, b, c]
    pos = apply_layout(nodes, get_preds, algorithm="grid")
    assert set(pos.keys()) == {"A", "B", "C"}
