from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.theme import get_theme_manager


def test_explicit_default_values_are_set(tmp_path):
    app = QApplication.instance() or QApplication([])
    s = QSettings("ComputationalGraphs", "GUI")

    # Ensure any persisted keys that could override the defaults are removed for this test
    keys = [
        "theme/bg",
        "theme/panel_bg",
        "theme/canvas_bg",
        "theme/header_bg",
        "theme/text",
        "theme/list_bg",
        "theme/accent",
        "theme/grid_color",
        "theme/edge_color",
        "theme/node_default",
        "theme/node_text",
    ]
    for k in keys:
        try:
            s.remove(k)
        except Exception:
            pass

    # Recreate manager to pick up cleared QSettings
    try:
        import ComputationalGraphs.GUI.theme as theme_module

        theme_module._manager = None
    except Exception:
        pass

    tm = get_theme_manager()

    assert tm.defaults["panel_bg"] == "#1e1e1e"
    assert tm.defaults["canvas_bg"] == "#161616"
    assert tm.defaults["grid_color"] == "#232323"
    assert tm.defaults["edge_color"] == "#505050"
    assert tm.defaults["header_bg"] == "#2c2c2c"
    assert tm.defaults["node_default"] == "#1497a3"
    assert tm.defaults["node_text"] == "#ffffff"
    assert tm.defaults["text"] == "#dcdcdc"
    assert tm.defaults["accent"] == "#00e3db"
