"""
Smoke test for screenshot capture functionality (headless).
"""

import os
import tempfile

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from ComputationalGraphs.GUI.main_window import MainWindow


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_capture_main_window(qapp, tmp_path):
    w = MainWindow()
    w.show()

    out = tmp_path / "main_window.png"
    # Use direct Qt grab to capture screenshot to file
    pix = w.grab()
    pix.save(str(out))

    assert out.exists()
    # Clean up
    w.close()
