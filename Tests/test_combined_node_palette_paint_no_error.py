from PyQt6.QtWidgets import QApplication, QWidget

from ComputationalGraphs.GUI.combined_node_palette import NodeItemWidget


def test_node_item_paint_executes_without_error():
    app = QApplication.instance() or QApplication([])
    parent = QWidget()
    w = NodeItemWidget("TestNode", "Addition", parent)
    w.show()
    # Trigger a paint and ensure no exceptions occur
    w.repaint()
    QApplication.processEvents()
    assert True
