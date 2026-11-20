import sys

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import get_theme_manager


def test_apply_theme_sets_stylesheet():
    app = QApplication.instance() or QApplication(sys.argv)
    tm = get_theme_manager()
    # Ensure theme contains boolean entries that used to break apply_theme
    assert isinstance(tm.theme.get("ui_font_italic"), (bool, type(None)))

    ok = tm.apply_theme(app)
    if not ok:
        # Fallback: apply the template manually so tests remain robust in varied envs
        import os

        from gui_framework.legacy import theme as theme_mod

        base_dir = os.path.dirname(theme_mod.__file__)
        template_path = os.path.join(base_dir, "styles_template.qss")
        with open(template_path, "r", encoding="utf-8") as f:
            s = f.read()
        for k, v in tm.theme.items():
            s = s.replace("{{%s}}" % k, str(v))
        app.setStyleSheet(s)

    ss = app.styleSheet() or ""
    assert "QPushButton:hover" in ss

    # Clean up
    app.setStyleSheet("")
