import pytest
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFontDialog

from gui_framework.legacy import ColorPreferencesDialog
from gui_framework.legacy import get_theme_manager


def test_choose_font_updates_button_and_theme(monkeypatch):
    # Ensure a QApplication exists for widget creation
    from PyQt6.QtWidgets import QApplication

    if QApplication.instance() is None:
        _app = QApplication([])
    tm = get_theme_manager()
    # Prepare a deterministic font selection
    f = QFont("DejaVu Sans", 15)
    f.setWeight(QFont.Weight.Medium)
    f.setItalic(True)

    # Monkeypatch/getFont override to return our font as if the user clicked OK
    orig = QFontDialog.getFont
    try:
        QFontDialog.getFont = lambda *args, **kwargs: (f, True)

        dlg = ColorPreferencesDialog(None)
        dlg.show()

        # Choose UI font via the dialog; the patched getFont will return our font
        dlg.choose_font("ui")
        # Process events so the button text update propagates in the test runner
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        app.processEvents()

        # Dialog's local theme must reflect the chosen font
        assert dlg.theme.get("ui_font_family") == "DejaVu Sans"
        assert dlg.theme.get("ui_font_size") == "15"
        assert dlg.theme.get("ui_font_italic") in (True, "True", "true")

        # The UI font exposed by ThemeManager may be normalized by the platform; accept
        # either the tm.get_font() family appearing in the button text, or the size in pt.
        ui_font = tm.get_font("ui")
        btn_text = dlg.ui_font_btn.text()
        assert (
            ui_font.family() in btn_text or f"{ui_font.pointSize()}pt" in btn_text
        ), f"Unexpected button label: {btn_text} (family: {ui_font.family()}, size: {ui_font.pointSize()})"
    finally:
        QFontDialog.getFont = orig
        try:
            dlg.close()
        except Exception:
            pass
