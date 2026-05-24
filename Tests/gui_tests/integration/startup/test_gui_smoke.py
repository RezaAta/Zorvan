"""
Simple headless smoke tests for New UI main window.
Runs in offscreen mode and ensures the MainWindow constructs and shows without raising.
"""

import os

import pytest

# Ensure headless mode set before importing PyQt
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from gui_framework import MainWindow


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_constructs(qapp):
    """MainWindow should construct and show without raising."""
    w = MainWindow()
    w.show()
    # basic assertion: instance exists and has expected attributes
    assert hasattr(w, "menuBar") or hasattr(w, "statusBar")
    # Close to clean up
    w.close()


def test_run_new_ui_imports(qapp):
    """Import run_new_ui and ensure it doesn't execute the event loop on import."""
    import importlib

    rn = importlib.import_module("run_new_ui")
    assert hasattr(rn, "main")
