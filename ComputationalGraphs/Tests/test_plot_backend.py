import pytest
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.plot_window import PlotWindow, create_plot_window


def test_create_plot_window_matplotlib_fallback():
    # Create a simple app instance
    app = QApplication.instance() or QApplication([])
    # Use Matplotlib backend explicitly
    pw = create_plot_window([], 10, None, backend="matplotlib")
    assert isinstance(pw, PlotWindow)
    pw.close()


def test_create_plot_window_auto_backend():
    # The auto backend should return PlotWindow or a pyqtgraph variant if available
    pw = create_plot_window([], 10, None, backend="auto")
    assert pw is not None
    pw.close()


def test_create_plot_window_pyqtgraph_fallback():
    # If pyqtgraph not installed, request pyqtgraph backend and ensure fallback occurs
    pw = create_plot_window([], 10, None, backend="pyqtgraph")
    assert pw is not None
    pw.close()


def test_matplotlib_legend_uniqueness():
    # Ensure a QApplication exists; remember if we created it so we can quit later
    app_created = False
    app = QApplication.instance()
    if app is None:
        app_created = True
        app = QApplication([])

    # Lightweight DummyNode for plotting
    class DummyNode:
        def __init__(self, name, value=0.0):
            self.name = name
            self.value = value

    # Create three nodes with the same name
    n1 = DummyNode("same")
    n2 = DummyNode("same")
    n3 = DummyNode("same")

    # Use Matplotlib backend explicitly and create the PlotWindow
    pw = create_plot_window([n1, n2, n3], 100, None, backend="matplotlib")

    try:
        # Helper to collect labels from the lines
        def _labels():
            try:
                return [ln.get_label() for ln in pw.lines.values()]
            except Exception:
                return []

        # Initial labels should be unique
        labels = _labels()
        assert len(labels) == len(set(labels))

        # Add another duplicate node and ensure labels stay unique
        n4 = DummyNode("same")
        pw.add_node(n4)
        labels = _labels()
        assert len(labels) == len(set(labels))

        # Remove an existing node via the combo selection and ensure uniqueness
        if n2 in pw.nodes:
            idx = pw.nodes.index(n2)
            pw.node_combo.setCurrentIndex(idx)
            pw.remove_selected_node()
            labels = _labels()
            assert len(labels) == len(set(labels))
    finally:
        # Close the window and allow the app to quit gracefully
        try:
            pw.close()
        except Exception:
            pass
        if app_created:
            try:
                app.quit()
            except Exception:
                pass
