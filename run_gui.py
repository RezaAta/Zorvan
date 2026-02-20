"""
Launch script for the Zorvan visual editor.
"""

import logging
import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from zorvan.GUI.main_window import MainWindow

logging.basicConfig(level=logging.INFO)


def main():
    """Main entry point for the GUI application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Zorvan")
    app.setOrganizationName("Zorvan")

    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "zorvan_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Load stylesheet (optional) and apply theme manager if available
    try:
        # Prefer the theme manager which will use a template if present
        try:
            from zorvan.GUI.theme import get_theme_manager

            tm = get_theme_manager()
            tm.apply_theme(app)
        except Exception:
            # Fallback to legacy static stylesheet
            style_path = os.path.join(
                os.path.dirname(__file__), "zorvan", "GUI", "styles.qss"
            )
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    app.setStyleSheet(f.read())
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning("Could not load stylesheet: %s", e)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
