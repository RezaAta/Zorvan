import os

import pytest

pytest.importorskip("PyQt6")
from PyQt6.QtWidgets import QApplication

from gui_framework.main_window import MainWindow
from gui_framework.window.manager import get_window_manager


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_registers_with_window_manager(qapp):
    manager = get_window_manager(qapp)
    window = MainWindow()

    assert manager.get_window("main") is window
    assert manager.get_active_window() is window

    manager.unregister_window("main")
