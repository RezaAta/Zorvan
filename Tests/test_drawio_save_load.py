import os
import tempfile

from ComputationalGraphs.Core.DrawioIO import DrawioIO
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.GUI.examples_loader import ExamplesLoader


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
