from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow, control_panel_builder, get_theme_manager


def test_persisted_theme_applies_on_mainwindow_startup():
    app = QApplication.instance() or QApplication([])

    # Append a simple handler to icon reapply handlers so we can verify it
    invoked = {"ran": False}

    def _fake_icon_reapply():
        invoked["ran"] = True

    control_panel_builder._ICON_REAPPLY_HANDLERS.append(_fake_icon_reapply)

    try:
        tm = get_theme_manager()
        # Persist a distinctive panel background color
        tm.set_theme({"panel_bg": "#0f1e2d"}, persist=True)

        mw = MainWindow()

        # Let event loop process updates
        app.processEvents()
        QTest.qWait(50)

        expected = tm.get_color("panel_bg").name()

        # Check dock background stylesheet contains expected color
        assert expected in mw.control_dock.widget().styleSheet()

        # Ensure our fake icon reapply handler was invoked during startup
        assert invoked["ran"] is True

    finally:
        # Clean up handler
        try:
            control_panel_builder._ICON_REAPPLY_HANDLERS.remove(_fake_icon_reapply)
        except Exception:
            pass
