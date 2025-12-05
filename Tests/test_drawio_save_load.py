import os
import tempfile

from ComputationalGraphs.Core.DrawioIO import DrawioIO
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.GUI.examples_loader import ExamplesLoader
from ComputationalGraphs.GUI.main_window import MainWindow


def test_drawio_save_load():
    loader = ExamplesLoader()
    # Use a simple graph (fibonacci)
    fib_graph = loader.categories["basic"].examples[0][2]()
    assert isinstance(fib_graph, Graph)

    # Save to temporary file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
    tmpname = tmp.name
    tmp.close()

    try:
        DrawioIO.save(fib_graph, tmpname)
        loaded = DrawioIO.load(tmpname)
        assert isinstance(loaded, Graph)
        assert len(loaded.nodes) == len(fib_graph.nodes)
        # Check basic node names exist
        orig_names = {n.name for n in fib_graph.nodes}
        loaded_names = {n.name for n in loaded.nodes}
        assert orig_names == loaded_names
    finally:
        try:
            os.remove(tmpname)
        except OSError:
            pass


def test_drawio_gui_visuals_preserved():
    loader = ExamplesLoader()
    fib_graph = loader.categories["basic"].examples[0][2]()
    # assign GUI positions and color to nodes
    for i, n in enumerate(fib_graph.nodes):
        n.gui_pos = (i * 100.0, i * 50.0)
        n.gui_color = "#112233"
        n.gui_label_color = "#ff00ff"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
    tmpname = tmp.name
    tmp.close()
    try:
        # Save with visuals
        DrawioIO.save(fib_graph, tmpname, preserve_visuals=True)
        loaded = DrawioIO.load(tmpname)
        # Visual properties should survive
        assert isinstance(loaded, Graph)
        assert len(loaded.nodes) == len(fib_graph.nodes)
        for orig, ld in zip(fib_graph.nodes, loaded.nodes):
            assert getattr(ld, "gui_pos", None) is not None
            assert tuple(map(float, ld.gui_pos)) == tuple(map(float, orig.gui_pos))
            assert getattr(ld, "gui_color", None) == orig.gui_color
            assert getattr(ld, "gui_label_color", None) == orig.gui_label_color
    finally:
        try:
            os.remove(tmpname)
        except OSError:
            pass


def test_drawio_save_load_gui_roundtrip():
    loader = ExamplesLoader()
    win = MainWindow()
    g = loader.categories["basic"].examples[1][2]()
    # assign GUI positions/colors to all nodes
    for idx, node in enumerate(g.nodes):
        node.gui_pos = (idx * 30.0, idx * 45.0)
        node.gui_color = "#123456"
        node.gui_radius = 40

    # Visualize graph on canvas to create node_items
    win._visualize_graph_on_canvas(g)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
    tmpname = tmp.name
    tmp.close()
    try:
        # Save file using FileIOController behaviour
        win.file_io_controller.graph = g
        # Use DrawioIO.save directly, passing canvas - CLI-based saving not tested here
        from ComputationalGraphs.Core.DrawioIO import DrawioIO

        DrawioIO.save(g, tmpname, canvas=win.canvas, preserve_visuals=True)
        # Clear canvas and reload from file through controller
        win.canvas.scene.clear()
        win.canvas.node_items.clear()
        win.canvas.edge_items.clear()
        win.file_io_controller._load_drawio(tmpname)

        # After loading, node_items must exist and carry manual_color and positions
        for node in win.graph.nodes:
            item = win.canvas.node_items.get(node)
            assert item is not None
            assert getattr(item, "manual_color", None) is not None
            assert isinstance(item.pos().x(), float)
            assert isinstance(item.pos().y(), float)
            # label color restored
            try:
                color = item.label.defaultTextColor().name()
            except Exception:
                color = None
            assert color == "#123456"
    finally:
        try:
            os.remove(tmpname)
        except OSError:
            pass
