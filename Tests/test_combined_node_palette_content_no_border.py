from PyQt6.QtWidgets import QApplication, QWidget

from zorvan.GUI.combined_node_palette import CombinedNodePalette


def test_category_content_has_no_border():
    app = QApplication.instance() or QApplication([])

    class DummyPalette:
        node_categories = {"Basic Operations": {"description": "", "nodes": []}}

    parent = QWidget()
    parent.palette = DummyPalette()
    palette = CombinedNodePalette(parent)

    panel = palette._category_panels.get("Basic Operations")
    assert panel is not None
    # The content style should NOT include a border property
    assert "border" not in panel.content.styleSheet().lower()
