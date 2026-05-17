"""Headless smoke test for PlotView rendering.

This test ensures that the PlotView can render in an offscreen Qt platform and
that the rendered screenshot can be opened by Pillow (verifies rendering and
Pillow integration). It avoids brittle baseline comparisons.
"""

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not (PYQT_AVAILABLE and PIL_AVAILABLE),
    reason="PyQt6 and Pillow required for smoke test",
)

from gui_framework.viewmodels.plot_viewmodel import PlotViewModel
from zorvan.GUI.plot_view import PlotView


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_plot_view_smoke_renders(qapp, tmp_path):
    vm = PlotViewModel()
    vm.add_node("A")
    vm.add_node("B")

    # Add some data
    for i in range(5):
        vm.add_data_point("A", float(i), iteration=i)
        vm.add_data_point("B", float(i * 2), iteration=i)

    view = PlotView(vm)

    # Force a paint and capture
    view.show()
    QApplication.processEvents()
    pix = view.grab()

    out = tmp_path / "plot_view_smoke.png"
    pix.save(str(out))

    # Ensure file exists and is openable by Pillow
    assert out.exists()
    img = Image.open(str(out))
    assert img.size[0] > 0 and img.size[1] > 0

    view.cleanup()
