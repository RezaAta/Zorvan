import pytest

# Skip GUI tests when PyQt6 isn't available in CI environments
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow


def test_examples_canvas_sync_xor_concurrent():
    # Headless app to ensure the GUI constructs widgets
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication([])
        owns_app = True
    mw = MainWindow()

    # Get the builder for local XOR concurrent example
    try:
        builder = mw.examples_loader._build_xor_mlp_concurrent
        name = "XOR Problem (2-2-1) - Concurrent"
    except Exception:
        # Try fallback search
        builder = None
        for cat in mw.examples_loader.get_categories():
            for ex_name, _, ex_builder in getattr(cat, "examples", []):
                if "xor" in ex_name.lower() and "concurrent" in ex_name.lower():
                    builder = ex_builder
                    name = ex_name
                    break
            if builder:
                break

    assert builder is not None, "Could not find XOR concurrent builder"

    # Load the example via MainWindow to create canvas items
    mw._load_example(builder, name)

    g = mw.graph
    c = mw.canvas

    # Basic checks: same number of nodes in graph and canvas map
    assert g is not None
    assert c is not None
    assert len(g.nodes) == len(
        c.node_items
    ), "Node count mismatch between Graph and Canvas"

    # Check every graph node has an id and is present in idToNodeDictionary and canvas mapping
    for node in g.nodes:
        assert getattr(node, "id", None) is not None
        assert node.id in g.idToNodeDictionary
        assert node in c.node_items

    # Clean up
    if owns_app:
        app.quit()
