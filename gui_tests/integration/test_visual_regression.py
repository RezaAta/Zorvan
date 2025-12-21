"""
Visual regression tests: compare current MainWindow and PlotWindow screenshots with baselines
using a tolerant pixel-difference threshold.
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

if PYQT_AVAILABLE:
    # Import compare_images from tests/utils/screenshot.py via importlib to avoid package issues
    import importlib.util
    from pathlib import Path

    from ComputationalGraphs.GUI.main_window import MainWindow
    from ComputationalGraphs.GUI.plot_window import PlotWindow

    # Locate tests/utils/screenshot.py by walking up until repo root
    p = Path(__file__).resolve()
    screenshot_path = None
    for parent in p.parents:
        candidate = parent / "tests" / "utils" / "screenshot.py"
        if candidate.exists():
            screenshot_path = candidate
            break
    if screenshot_path is None:
        raise FileNotFoundError("Could not find tests/utils/screenshot.py")

    spec = importlib.util.spec_from_file_location(
        "screenshot_utils", str(screenshot_path)
    )
    screenshot_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(screenshot_utils)
    compare_images = screenshot_utils.compare_images


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


BASE = Path(__file__).resolve().parents[1] / "baselines"
TOLERANCE = 0.02  # Allow up to 2% pixel difference


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _capture_widget(widget, path: Path):
    widget.show()
    QApplication.processEvents()
    pix = widget.grab()
    pix.save(str(path))


def test_main_window_visual_matches(qapp, tmp_path):
    baseline = BASE / "main_window_baseline.png"
    assert (
        baseline.exists()
    ), f"Baseline missing: {baseline}. Run tools/generate_gui_baselines.py to create it."

    w = MainWindow()
    cur = tmp_path / "main_window.png"
    _capture_widget(w, cur)
    ok, ratio = compare_images(str(baseline), str(cur), max_diff_ratio=TOLERANCE)
    w.close()
    assert ok, f"MainWindow visual diff too large: {ratio:.4f} > {TOLERANCE}"


def test_plot_window_visual_matches(qapp, tmp_path):
    baseline = BASE / "plot_window_baseline.png"
    assert (
        baseline.exists()
    ), f"Baseline missing: {baseline}. Run tools/generate_gui_baselines.py to create it."

    # Build a similar plot state as baseline
    class DummyNode:
        def __init__(self, name):
            self.name = name
            self.value = 0.0

    nodes = [DummyNode("A"), DummyNode("B")]
    plot = PlotWindow(nodes, max_iterations=50)

    for it in range(10):
        nodes[0].value = float(it)
        nodes[1].value = float(2 * it + 1)
        plot.update_plot(it)
        QApplication.processEvents()

    cur = tmp_path / "plot_window.png"
    _capture_widget(plot, cur)
    ok, ratio = compare_images(str(baseline), str(cur), max_diff_ratio=TOLERANCE)
    plot.close()
    assert ok, f"PlotWindow visual diff too large: {ratio:.4f} > {TOLERANCE}"
