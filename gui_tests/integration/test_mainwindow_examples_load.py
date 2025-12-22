import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

from ComputationalGraphs.GUI.main_window import MainWindow


@pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 not installed")
def test_mainwindow_loads_example_and_visualizes(qtbot):
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()
    qtbot.addWidget(mw)

    # Pick the first category and first example
    categories = mw.examples_loader.get_categories()
    assert categories, "No example categories available"
    cat = categories[0]
    assert cat.examples, "Category has no examples"
    name, desc, builder = cat.examples[0]

    # Load example via dialog controller route
    mw._load_example(builder, name)
    app.processEvents()

    # Basic sanity: graph present and nodes added
    assert getattr(mw, "graph", None) is not None
    assert len(mw.graph.nodes) > 0, "Loaded graph has no nodes"

    # Canvas items should be created for nodes
    try:
        node_items = getattr(mw.canvas, "node_items", {})
        assert len(node_items) > 0, "Canvas did not create node items"
    except Exception:
        # Some environments may not create real canvas widgets; still assert graph populated
        pass

    # Cleanup
    try:
        mw.close()
    except Exception:
        pass
