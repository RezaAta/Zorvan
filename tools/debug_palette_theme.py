from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow, get_theme_manager, ColorPreferencesDialog

app = QApplication.instance() or QApplication([])
get_theme_manager()  # ensure manager is initialized
mw = MainWindow()
print("Theme keys sample:", sorted(list(get_theme_manager().theme.keys()))[:10])
pal = getattr(mw, "combined_palette", None)
if pal is None:
    print("No combined_palette present")
else:
    tc = pal._theme_colors
    print("CombinedNodePalette._theme_colors keys:", list(tc.keys()))
    try:
        print("node_bg:", tc["node_bg"].name())
    except Exception:
        print("node_bg missing or not QColor")

# Examine QSettings stored value for node_default
from PyQt6.QtCore import QSettings

s = QSettings("ComputationalGraphs", "GUI")
print("QSettings node_default:", s.value("theme/node_default", None))
print("QSettings node_text:", s.value("theme/node_text", None))
print("QSettings panel_bg:", s.value("theme/panel_bg", None))
print("ThemeManager.theme node_default:", get_theme_manager().theme.get("node_default"))

# Now instantiate ColorPreferences dialog and simulate applying without user interaction
try:
    from gui_framework.legacy import ColorPreferencesDialog

    dlg = ColorPreferencesDialog(None)
    dlg.set_color_for_key("node_default", "#445566", apply_theme=True)
    print(
        "After set, palette node_bg:",
        mw.combined_palette._theme_colors["node_bg"].name(),
    )
except Exception as e:
    print("ColorPreferencesDialog not available:", e)
print("Done")
