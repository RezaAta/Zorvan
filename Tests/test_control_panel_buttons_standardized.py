import sys

from PyQt6.QtWidgets import QApplication, QPushButton

from ComputationalGraphs.GUI.main_window import MainWindow


def ensure_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_control_panel_buttons_have_no_inline_hover_styles():
    app = ensure_app()
    mw = MainWindow()

    from PyQt6.QtWidgets import QWidget

    control_panel = mw.findChild(QWidget, "controlPanel")
    assert control_panel is not None

    buttons = control_panel.findChildren(QPushButton)
    # Ensure we actually found some buttons to validate
    assert len(buttons) > 0

    for btn in buttons:
        ss = btn.styleSheet()
        # Inline hover styles should not be injected; rely on global QSS instead
        if "background-color" in ss:
            # Some color swatch buttons intentionally have inline background to
            # display the color; those are allowed to have background-color set.
            name = (btn.objectName() or "").lower()
            text = (btn.text() or "").lower()
            allowed = any(k in name for k in ["swatch", "color", "gradient"]) or any(
                k in text for k in ["color", "min", "max", "gradient"]
            )
            # Allow compact color swatch buttons that display color but have no text
            if not allowed:
                allowed = btn.text().strip() == "" and ss.strip().startswith(
                    "background-color:"
                )
            assert (
                allowed
            ), f"Unexpected inline background-style on button '{btn.objectName()}' text='{btn.text()}' ss='{ss}'"
        assert ":hover" not in ss

    # Clean up
    mw.close()
    app.quit()
