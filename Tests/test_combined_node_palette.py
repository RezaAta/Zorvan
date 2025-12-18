from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.combined_node_palette import CombinedNodePalette


def test_combined_palette_populates_from_parent_categories():
    app = QApplication.instance() or QApplication([])

    class DummyPalette:
        node_categories = {
            "Test Category": {
                "description": "A test category",
                "nodes": [("FooNode", "Foo", "Test node")],
            }
        }

    from PyQt6.QtWidgets import QWidget

    parent = QWidget()
    # attach palette-like attribute used by CombinedNodePalette
    parent.palette = DummyPalette()
    palette = CombinedNodePalette(parent)

    # There should be one node widget populated
    assert len(palette._node_widgets) == 1
    widget, category, name = palette._node_widgets[0]
    assert category == "Test Category"
    assert name == "foo"
    assert widget.display_name == "Foo"
