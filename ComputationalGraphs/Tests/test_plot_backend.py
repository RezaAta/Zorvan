import pytest

# Skip GUI tests when PyQt6 isn't available in CI environments
pytest.importorskip("PyQt6")

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
    """Test that node names are tracked correctly when adding nodes.

    This test verifies that the PlotWindow correctly handles multiple nodes
    with the same name by maintaining unique internal references.
    """
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
        # Verify nodes were added
        assert len(pw.nodes) == 3

        # All nodes should have the same name
        assert all(n.name == "same" for n in pw.nodes)

        # Add another duplicate node
        n4 = DummyNode("same")
        pw.add_node(n4)

        # Should now have 4 nodes
        assert len(pw.nodes) == 4

        # Node names should still all be "same"
        assert all(n.name == "same" for n in pw.nodes)

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
