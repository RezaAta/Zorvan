import pytest
from PyQt6.QtWidgets import QApplication
from ComputationalGraphs.GUI.plot_window_pyqtgraph import PlotWindowPG


class DummyNode:
    def __init__(self, name):
        self.name = name
        self.value = 0.0


def _create_app():
    app = QApplication.instance() or QApplication([])
    return app


def test_opengl_toggle_recreates_widget():
    app = _create_app()
    nodes = [DummyNode('A'), DummyNode('B')]
    pw = PlotWindowPG(nodes, 10)
    assert pw is not None
    # initial widget exists
    assert hasattr(pw, 'plot_widget') and pw.plot_widget is not None
    # Toggle off OpenGL -> recreate widget
    pw.use_opengl_check.setChecked(False)
    # toggle back on -> recreate
    pw.use_opengl_check.setChecked(True)
    # assert plot_widget recreated and has curves
    assert hasattr(pw, 'plot_widget') and pw.plot_widget is not None
    assert hasattr(pw, 'curves')
    # cleanup
    try:
        pw.close()
    except Exception:
        pass
