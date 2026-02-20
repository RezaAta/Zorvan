from PyQt6.QtWidgets import QApplication, QWidget

from zorvan.GUI.combined_node_palette import CombinedNodePalette


def test_categories_default_state():
    app = QApplication.instance() or QApplication([])

    class DummyPalette:
        node_categories = {
            "Basic Operations": {"description": "", "nodes": []},
            "Data & Buffers": {"description": "", "nodes": []},
            "Activation Functions": {"description": "", "nodes": []},
        }

    parent = QWidget()
    parent.palette = DummyPalette()
    palette = CombinedNodePalette(parent)

    panels = palette._category_panels
    assert "Basic Operations" in panels
    assert panels["Basic Operations"].header.isChecked() is True
    # All others closed
    for name, panel in panels.items():
        if name != "Basic Operations":
            assert panel.header.isChecked() is False
