from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import GraphCanvas


def test_default_grid_and_snap():
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication([])
        created_app = True
    canvas = GraphCanvas(None)
    assert canvas.grid_mode == "4x4"
    assert canvas.grid_size == max(1, int(canvas.node_diameter / 4))
    assert canvas.snap_step == 1
    canvas.deleteLater()
    app.processEvents()
    if created_app:
        app.quit()
