import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from PyQt6.QtCore import QSettings

from zorvan.GUI import theme as theme_module


def test_defaults_honor_saved_qsettings(tmp_path):
    app = QApplication.instance() or QApplication([])
    s = QSettings("ComputationalGraphs", "GUI")

    # Set a couple of saved theme values
    s.setValue("theme/node_default", "#123456")
    s.setValue("theme/node_text", "#abcdef")

    # Reset the module singleton to force reinitialization
    try:
        theme_module._manager = None
    except Exception:
        pass

    tm = theme_module.get_theme_manager()

    # The in-code defaults should reflect the stored QSettings
    assert tm.defaults.get("node_default") == "#123456"
    assert tm.defaults.get("node_text") == "#abcdef"

    # Cleanup
    try:
        s.remove("theme/node_default")
        s.remove("theme/node_text")
    except Exception:
        pass
    try:
        theme_module._manager = None
    except Exception:
        pass
