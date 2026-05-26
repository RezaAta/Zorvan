from PyQt6.QtWidgets import QApplication, QWidget

from gui_framework.legacy import CombinedNodePalette, NodeItemWidget, get_theme_manager


def test_palette_auto_applies_theme_on_construction():
    app = QApplication.instance() or QApplication([])

    # Set theme values before constructing the palette
    tm = get_theme_manager()
    tm.set_theme({"node_default": "#445566", "node_text": "#aabbcc"}, persist=False)

    class DummyPalette:
        node_categories = {
            "Basic Operations": {
                "description": "",
                "nodes": [("AdditionNode", "Addition", "Adds")],
            }
        }

    parent = QWidget()
    parent.palette = DummyPalette()
    palette = CombinedNodePalette(parent)

    # After construction, theme colors must be applied without manual palette.apply_theme()
    assert palette._theme_colors["node_text"].name() == "#aabbcc"

    # Node widgets should repaint without raising and use the theme colors
    w = NodeItemWidget("AdditionNode", "Addition", "Adds values", palette)
    palette._node_widgets.append((w, "Basic Operations", "addition"))
    w.repaint()
    app.processEvents()
    assert palette._theme_colors["node_text"].name() == "#aabbcc"
