"""
Run the "New UI" main window with convenient CLI options.

Usage:
    python run_new_ui.py [--example <name>] [--maximize] [--debug]

Options:
    --example <name>   Auto-load an example by name
    --maximize         Start the main window maximized
    --debug            Enable debug logging to the console

This script is intentionally lightweight and serves as the canonical launcher for the
new UI. It provides some convenience options useful during Phase-5 manual QA.
"""

import argparse
import logging
import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from gui_framework.main_window import MainWindow
from gui_framework.window.manager import get_window_manager


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the ComputationalGraphs New UI")
    parser.add_argument(
        "--example", type=str, help="Name of example to auto-load", default=None
    )
    parser.add_argument(
        "--maximize", action="store_true", help="Start window maximized"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args(argv)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().debug("Debug logging enabled")

    def resource_path(relative_path: str) -> str:
        if getattr(sys, "frozen", False):
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, relative_path)

    # High DPI handling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Computational Graphs Editor (New UI)")
    app.setOrganizationName("ComputationalGraphs")

    # Prefer the ICO artifact, but fall back to PNG if needed.
    icon_candidates = [
        resource_path(os.path.join("assets", "zorvan.ico")),
        resource_path(os.path.join("assets", "ZorvanIcon.png")),
        resource_path(os.path.join("assets", "ZorvanLogoTransparent.png")),
    ]
    for icon_path in icon_candidates:
        if os.path.exists(icon_path):
            try:
                app.setWindowIcon(QIcon(icon_path))
                break
            except Exception:
                continue

    # Apply theme if available
    try:
        from gui_framework.theme import get_theme_manager

        tm = get_theme_manager()
        tm.apply_theme(app)
    except Exception:
        # Fallback to the old stylesheet on failure
        try:
            style_path = os.path.join(
                os.path.dirname(__file__), "ComputationalGraphs", "GUI", "styles.qss"
            )
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    app.setStyleSheet(f.read())
        except Exception:
            pass

    window = MainWindow()
    manager = get_window_manager(app)

    # Optionally maximize
    if args.maximize:
        try:
            window.showMaximized()
        except Exception:
            manager.show_window("main")
    else:
        manager.show_window("main")

    # Optionally load an example (best-effort)
    if args.example:
        try:
            # Examples loader is exposed on MainWindow via ExamplesLoader
            window._load_example(
                window.examples_loader.get_example_builder(args.example), args.example
            )
        except Exception as e:
            logging.getLogger().warning(
                "Failed to auto-load example '%s': %s", args.example, e
            )

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
