"""
Launch script for the ComputationalGraphs visual editor.
"""

import logging
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow

logging.basicConfig(level=logging.INFO)


def main():
    """Main entry point for the GUI application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Computational Graphs Editor")
    app.setOrganizationName("ComputationalGraphs")

    # Load stylesheet (optional) and apply theme manager if available
    try:
        # Prefer the theme manager which will use a template if present
        try:
            from ComputationalGraphs.GUI.theme import get_theme_manager

            tm = get_theme_manager()
            tm.apply_theme(app)
        except Exception:
            # Fallback to legacy static stylesheet
            import os

            style_path = os.path.join(
                os.path.dirname(__file__), "ComputationalGraphs", "GUI", "styles.qss"
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
