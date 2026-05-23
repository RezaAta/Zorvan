from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from zorvan.GUI.theme import get_theme_manager


def test_save_as_default_updates_defaults():
    app = QApplication.instance() or QApplication([])
    s = QSettings("ComputationalGraphs", "GUI")

    # Clear keys that may affect the test
    try:
        s.remove("theme/node_default")
        s.remove("theme/node_text")
    except Exception:
        pass

    # Reset manager
    import zorvan.GUI.theme as theme_module

    try:
        theme_module._manager = None
    except Exception:
        pass

    tm = get_theme_manager()
    old = tm.defaults.get("node_default")

    # Save a new theme value and persist it
    new_theme = dict(tm.theme)
    new_theme["node_default"] = "#112233"
    new_theme["node_text"] = "#aabbcc"
    tm.save_theme(new_theme)

    # After save_theme, defaults should be updated immediately
    assert tm.defaults.get("node_default") == "#112233"
    assert tm.defaults.get("node_text") == "#aabbcc"

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
