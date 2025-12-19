from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QPushButton

from ComputationalGraphs.GUI.color_preferences import ColorPreferencesDialog
from ComputationalGraphs.GUI.controllers.control_panel_builder import _apply_icon


def _icon_color_hex(btn: QPushButton) -> str:
    icon = btn.icon()
    pm = icon.pixmap(QSize(16, 16))
    img = pm.toImage()
    w = img.width()
    h = img.height()
    # Find first non-transparent pixel and return its color
    for y in range(h):
        for x in range(w):
            c = img.pixelColor(x, y)
            if c.alpha() > 0:
                return c.name()
    # Fallback to center pixel if all transparent
    return img.pixelColor(w // 2, h // 2).name()


def test_accent_changes_icon_color():
    app = QApplication.instance() or QApplication([])
    btn = QPushButton()
    # Set known initial accent and apply it
    dlg = ColorPreferencesDialog()
    dlg.set_color_for_key("accent", "#00ff00", apply_theme=True)

    # apply an icon using fontawesome name (may fallback to style pixmap)
    _apply_icon(btn, btn, "fa5s.plus", None, size_px=16, color_key="accent")

    # Process events using the existing QApplication instance
    app.processEvents()

    old_col = _icon_color_hex(btn)

    # Change accent color via ColorPreferencesDialog helper to a different value
    dlg.set_color_for_key("accent", "#ff00ff", apply_theme=True)
    QApplication.processEvents()

    new_col = _icon_color_hex(btn)

    assert (
        old_col != new_col
    ), f"Icon color should update when accent changes (old={old_col}, new={new_col})"
