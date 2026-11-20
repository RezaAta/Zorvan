from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QPushButton

print("TEST_IMPORT: test_icon_accent_updates import start")

from gui_framework.legacy import _apply_icon
from gui_framework.legacy.color_preferences import ColorPreferencesDialog


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

    # Ensure initial handler has run at least once so the deterministic attribute is set
    try:
        from gui_framework.legacy import _ICON_REAPPLY_HANDLERS

        for h in list(_ICON_REAPPLY_HANDLERS):
            try:
                h()
            except Exception:
                pass
    except Exception:
        pass

    # Process events using the existing QApplication instance
    app.processEvents()

    old_col = _icon_color_hex(btn)
    old_attr = getattr(btn, "_last_applied_icon_color", None)

    # Change accent color via ColorPreferencesDialog helper to a different value
    dlg.set_color_for_key("accent", "#ff00ff", apply_theme=True)
    QApplication.processEvents()

    # Prefer reliable attribute if present (set by deterministic reapply); otherwise sample pixels
    new_attr = getattr(btn, "_last_applied_icon_color", None)
    if new_attr is not None and old_attr is not None:
        assert (
            old_attr.lower() != new_attr.lower()
        ), f"Icon color should update when accent changes (old={old_attr}, new={new_attr})"
    else:
        new_col = _icon_color_hex(btn)
        assert (
            old_col != new_col
        ), f"Icon color should update when accent changes (old={old_col}, new={new_col})"
