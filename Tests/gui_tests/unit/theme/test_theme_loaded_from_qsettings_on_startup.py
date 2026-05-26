from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QWidget

from gui_framework.legacy import MainWindow, get_theme_manager


def test_theme_loaded_from_qsettings_applies_to_ui_on_startup():
    app = QApplication.instance() or QApplication([])
    s = QSettings("ComputationalGraphs", "GUI")

    # Persist some theme values as if user saved them previously
    s.setValue("theme/panel_bg", "#112233")
    s.setValue("theme/node_default", "#445566")
    s.setValue("theme/accent", "#00ff00")

    # Ensure singleton will be re-created to pick up fresh settings
    from gui_framework.legacy import theme as theme_module

    try:
        theme_module._manager = None
    except Exception:
        pass

    tm = get_theme_manager()

    # Theme manager's in-memory theme should contain persisted values
    assert tm.theme.get("panel_bg") == "#112233"
    assert tm.theme.get("node_default") == "#445566"
    assert tm.theme.get("accent") == "#00ff00"

    # Create a MainWindow - its CombinedNodePalette should honor persisted theme
    mw = MainWindow()
    pal = getattr(mw, "combined_palette", None)
    assert pal is not None

    # Ensure the palette's cached theme colors include the persisted node_default
    # node_default may be stored as QColor in palette._theme_colors; accept either
    nd = pal._theme_colors.get("node_bg")
    if hasattr(nd, "name"):
        assert nd.name() == "#445566"
    else:
        assert nd == "#445566"

    # Cleanup
    try:
        s.remove("theme/panel_bg")
        s.remove("theme/node_default")
        s.remove("theme/accent")
    except Exception:
        pass
    try:
        theme_module._manager = None
    except Exception:
        pass
