from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import get_theme_manager


def test_apply_theme_debug():
    app = QApplication.instance() or QApplication([])
    tm = get_theme_manager()
    rv = tm.apply_theme()
    ss = app.styleSheet() or ""
    print("\n[DEBUG] tm.apply_theme returned", rv)
    print("[DEBUG] app.styleSheet length", len(ss))
    assert 'QPushButton[themed="true"]:hover' in ss
