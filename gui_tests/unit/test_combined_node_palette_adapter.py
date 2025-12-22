import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for adapter tests")

from ComputationalGraphs.GUI.combined_node_palette_adapter import (
    CombinedNodePaletteAdapter,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_combined_palette_adapter_constructs(qapp):
    adapter = CombinedNodePaletteAdapter()
    w = adapter.widget()
    assert w is not None
    cats = adapter.get_categories()
    assert isinstance(cats, dict)
    # Try setting search text and calling close
    adapter.set_search_text("relu")
    adapter.close()
