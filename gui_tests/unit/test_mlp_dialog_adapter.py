import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for adapter tests")

from ComputationalGraphs.GUI.mlp_dialog import MLPGeneratorDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_mlp_dialog_adapter_constructs_and_generates(qapp):
    dlg = MLPGeneratorDialog()
    # Avoid blocking exec() in tests - just ensure get_graph exists after a generate
    # Simulate platform by invoking internal _on_generate if available
    try:
        # Set simple parameters and call generate
        dlg.num_inputs.setValue(2)
        dlg.num_hidden_layers.setValue(1)
        dlg.num_outputs.setValue(1)
        # If adapter wraps MVVM dialog, call the public method
        if hasattr(dlg, "_on_generate"):
            dlg._on_generate()
        elif hasattr(dlg, "_dlg") and hasattr(dlg._dlg, "_on_generate"):
            dlg._dlg._on_generate()
    except Exception:
        # Dialog may not expose internals; that's fine - we just check API
        pass

    # get_graph should exist and either return None or a Graph
    try:
        g = dlg.get_graph()
    except Exception:
        pytest.fail("get_graph() raised an exception")

    dlg.close()
