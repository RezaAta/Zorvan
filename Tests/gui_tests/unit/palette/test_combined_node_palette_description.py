from PyQt6.QtWidgets import QApplication, QWidget

from gui_framework.legacy import CombinedNodePalette
from gui_framework.legacy import get_short_name


def test_palette_uses_short_names_and_shows_description():
    app = QApplication.instance() or QApplication([])

    class DummyPalette:
        node_categories = {
            "Data & Buffers": {
                "description": "Data sources and storage containers",
                "nodes": [
                    (
                        "DynamicDataStreamNode",
                        "Dynamic Data Stream",
                        "Dynamic data source with runtime updates",
                    )
                ],
            }
        }

    parent = QWidget()
    parent.palette = DummyPalette()
    palette = CombinedNodePalette(parent)

    # Find the NodeItemWidget
    widgets = [w for w, c, _ in palette._node_widgets]
    assert len(widgets) == 1
    w = widgets[0]

    # Short name should match shared mapping
    assert w.short_name == get_short_name("DynamicDataStreamNode")

    # Show description via palette and verify popup text
    palette.show_description(w.display_name, w.description, w)
    popup = palette._description_popup
    assert popup is not None
    assert "Dynamic Data Stream" in popup.text()
    assert "runtime updates" in popup.text()
    # Hide and ensure no exception
    palette.hide_description()
    assert not popup.isVisible()
