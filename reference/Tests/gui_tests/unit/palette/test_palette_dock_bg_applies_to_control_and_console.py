from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import ColorPreferencesDialog, MainWindow


def test_dock_bg_applies_to_control_and_console():
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()

    dlg = ColorPreferencesDialog(mw)
    # Set the single authoritative panel background and apply
    dlg.set_color_for_key("panel_bg", "#0f1e2d", apply_theme=True)

    # Force palettes to refresh
    try:
        mw.control_panel_builder.mw.control_dock.widget().update()
    except Exception:
        pass

    # The control & console docks should reflect the current panel_bg value
    from gui_framework.legacy import get_theme_manager

    tm = get_theme_manager()
    current = tm.theme.get("panel_bg")
    assert current is not None
    # Ensure the event loop processed theme changes
    app = QApplication.instance()
    if app is not None:
        app.processEvents()
    # Give a little extra time for widget stylesheet updates in CI/slow envs
    QTest.qWait(100)
    expected = tm.get_color("panel_bg").name()
    # Poll for up to ~300ms to allow asynchronous updates to propagate in slow
    # environments (CI, headless). This reduces flaky failures.
    found = False
    for _ in range(10):
        app.processEvents()
        if expected in mw.control_dock.widget().styleSheet():
            found = True
            break
        QTest.qWait(20)
    assert (
        found
    ), f"Expected panel_bg {expected} in control dock stylesheet, got {mw.control_dock.widget().styleSheet()}"
    assert current in mw.console_dock.widget().styleSheet()
