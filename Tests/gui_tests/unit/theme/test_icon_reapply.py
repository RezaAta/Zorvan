import pytest

print("TEST_IMPORT: test_icon_reapply import start")
pytest.importorskip("PyQt6")

from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import _create_standard_button, get_theme_manager


def _pixmap_color_hex(pm: QPixmap):
    img = pm.toImage()
    # sample center pixel
    w = img.width() // 2
    h = img.height() // 2
    c = img.pixelColor(w, h)
    return c.name()


def test_icon_recolors_on_accent_change():
    app = QApplication.instance() or QApplication([])
    tm = get_theme_manager()

    # Create a temporary widget and button with an icon (uses _apply_icon internally)
    class W:
        pass

    w = W()

    btn = _create_standard_button(w, "I", "fa5s.info", None, 14)
    # Ensure we can get an initial pixmap
    pm0 = btn.icon().pixmap(14, 14)
    assert not pm0.isNull()
    c0 = _pixmap_color_hex(pm0)

    # Change accent color and apply theme
    old = tm.theme.get("accent")
    try:
        tm.set_theme({"accent": "#ff0000"}, persist=False)
        tm.apply_theme()
        # Force any registered handlers to run to ensure deterministic reapply in tests
        try:
            from gui_framework.legacy import _ICON_REAPPLY_HANDLERS

            for h in list(_ICON_REAPPLY_HANDLERS):
                try:
                    h()
                except Exception:
                    pass
        except Exception:
            pass
        pm1 = btn.icon().pixmap(14, 14)
        c1 = _pixmap_color_hex(pm1)
        assert c0 != c1
    finally:
        tm.set_theme({"accent": old}, persist=False)
        tm.apply_theme()
