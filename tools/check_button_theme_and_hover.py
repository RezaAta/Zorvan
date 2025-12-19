import json

# Ensure repo root is on sys.path
import os
import sys

root = os.path.dirname(os.path.dirname(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

# Lazily create QApplication if needed
app = QApplication.instance() or QApplication([])

# Import after QApplication so any widget creation works
from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.GUI.theme import get_theme_manager

# Apply theme to ensure stylesheet tokens are present
tm = get_theme_manager()
# Force a known theme for diagnostics
tm.set_theme(
    {"button_bg": "#101010", "button_hover": "#202020", "button_pressed": "#303030"},
    persist=False,
)
tm.apply_theme()

# Create main window
mw = MainWindow()
app.processEvents()

out = {}


# Helper
def inspect_btn(btn):
    from PyQt6.QtGui import QPalette

    try:
        palette_button = btn.palette().color(QPalette.ColorRole.Button).name()
    except Exception:
        palette_button = None
    try:
        bg_role = btn.backgroundRole()
    except Exception:
        bg_role = None
    try:
        parent_cls = type(btn.parent()).__name__
    except Exception:
        parent_cls = None
    return {
        "type": str(type(btn)),
        "themed_property": bool(btn.property("themed")),
        "inline_stylesheet": bool(btn.styleSheet()),
        "stylesheet_preview": btn.styleSheet()[:200] if btn.styleSheet() else "",
        "cursor_shape": (
            btn.cursor().shape().name
            if hasattr(btn.cursor().shape(), "name")
            else str(btn.cursor().shape())
        ),
        "palette_button_color": palette_button,
        "background_role": str(bg_role),
        "parent_class": parent_cls,
        "is_flat": getattr(btn, "isFlat", lambda: False)(),
        "is_checkable": getattr(btn, "isCheckable", lambda: False)(),
        "size": [btn.width(), btn.height()],
    }


out["app_stylesheet_contains_themed_hover_selector"] = (
    'QPushButton[themed="true"]:hover' in (app.styleSheet() or "")
)
out["app_stylesheet_contains_toolbutton_hover_selector"] = (
    'QToolButton[themed="true"]:hover' in (app.styleSheet() or "")
)
out["app_stylesheet_contains_hover_color"] = tm.get_color("button_hover").name() in (
    app.styleSheet() or ""
)

# Inspect toolbar add-to-plot button
try:
    toolbar_btn = mw.toolbar_add_to_plot_btn
    out["toolbar_add_to_plot"] = inspect_btn(toolbar_btn)
except Exception as e:
    out["toolbar_add_to_plot_error"] = repr(e)

# Inspect control panel play button
try:
    play_btn = mw.play_btn
    out["control_play_btn"] = inspect_btn(play_btn)
except Exception as e:
    out["control_play_btn_error"] = repr(e)

print(json.dumps(out, indent=2))

# Keep the window alive briefly if run interactively
# app.exec()

# Exit cleanly
sys.exit(0)
