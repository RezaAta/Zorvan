from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow


def test_examples_canvas_sync_xor_concurrent():
    # Headless app to ensure the GUI constructs widgets
    app = QApplication([])
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
    app.quit()
