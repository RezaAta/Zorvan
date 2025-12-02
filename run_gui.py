"""
Launch script for the ComputationalGraphs visual editor.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ComputationalGraphs.GUI.main_window import MainWindow


def main():
    """Main entry point for the GUI application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Computational Graphs Editor")
    app.setOrganizationName("ComputationalGraphs")
    
    # Load stylesheet (optional)
    try:
        import os
        style_path = os.path.join(os.path.dirname(__file__),
                                 "ComputationalGraphs", "GUI", "styles.qss")
        if os.path.exists(style_path):
            with open(style_path, 'r') as f:
                app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Could not load stylesheet: {e}")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
