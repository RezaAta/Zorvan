try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

import pytest

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from gui_framework.legacy import get_theme_manager
from gui_framework.legacy import ThemedProgressBar


def test_progress_bar_uses_accent_color(qtbot):
    app = QApplication.instance() or QApplication([])
    pb = ThemedProgressBar()
    qtbot.addWidget(pb)

    tm = get_theme_manager()
    accent = tm.get_color("accent").name()

    assert accent in pb.styleSheet()
