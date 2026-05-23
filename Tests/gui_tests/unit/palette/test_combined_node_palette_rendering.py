from PyQt6.QtWidgets import QApplication, QWidget

from zorvan.GUI.combined_node_palette import NodeItemWidget


def test_node_item_size_and_paint_callable():
    app = QApplication.instance() or QApplication([])
    w = NodeItemWidget("TestNode", "XOR", "XOR gate")
    # sizeHint should match expected diameter
    assert w.sizeHint().width() == w.NODE_DIAMETER
    assert w.sizeHint().height() == w.NODE_DIAMETER
    # paintEvent should be a callable attribute
    assert callable(getattr(w, "paintEvent", None))
