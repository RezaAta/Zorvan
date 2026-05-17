from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel


class SimpleNode:
    def __init__(self, name, preds=None):
        self.name = name
        self.predecessors = preds or []


class SimpleGraph:
    def __init__(self, nodes):
        self.nodes = nodes


def test_canvas_apply_grid_layout_updates_positions():
    a = SimpleNode("A")
    b = SimpleNode("B", preds=[a])
    c = SimpleNode("C", preds=[b])
    g = SimpleGraph([a, b, c])

    vm = CanvasViewModel(g)
    vm.initialize()

    # Ensure nodes loaded with default (0,0)
    nodes = {n.node_id: (n.x, n.y) for n in vm.get_nodes()}
    assert nodes["A"] == (0.0, 0.0)

    # Apply grid layout
    positions = vm.apply_layout(algorithm="grid", cols=2, spacing=100)
    assert positions is not None

    # After applying, nodes should have non-zero positions
    new_nodes = {n.node_id: (n.x, n.y) for n in vm.get_nodes()}
    assert any(x != 0.0 or y != 0.0 for x, y in new_nodes.values())

    # Ensure returned mapping matches node ids
    assert set(positions.keys()) == {"A", "B", "C"}
