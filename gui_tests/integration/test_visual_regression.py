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

# Import compare_images from tests/utils/screenshot.py via importlib to avoid package issues
import importlib.util
from pathlib import Path

if PYQT_AVAILABLE:
    from ComputationalGraphs.GUI.main_window import MainWindow
    from ComputationalGraphs.GUI.plot_window import PlotWindow
else:
    MainWindow = None
    PlotWindow = None

# Locate tests/utils/screenshot.py by walking up until repo root; accept both 'tests' and 'Tests'
p = Path(__file__).resolve()
screenshot_path = None
for parent in p.parents:
    for subdir in ("tests", "Tests"):
        candidate = parent / subdir / "utils" / "screenshot.py"
        if candidate.exists():
            screenshot_path = candidate
            break
    if screenshot_path:
        break
if screenshot_path is None:
    raise FileNotFoundError("Could not find tests/ or Tests/ utils/screenshot.py")

spec = importlib.util.spec_from_file_location("screenshot_utils", str(screenshot_path))
screenshot_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screenshot_utils)
compare_images = screenshot_utils.compare_images
PIL_AVAILABLE = getattr(screenshot_utils, "PIL_AVAILABLE", False)

# Skip tests if PyQt6 or Pillow is not available
pytestmark = pytest.mark.skipif(
    not (PYQT_AVAILABLE and PIL_AVAILABLE),
    reason="PyQt6 and Pillow are required for visual regression tests",
)


BASE = Path(__file__).resolve().parents[1] / "baselines"
# Configurable tolerance values: can be overridden by environment variables for CI
TOLERANCE = float(
    os.getenv("VISUAL_MAX_DIFF_RATIO", "0.02")
)  # default 2% pixel difference
PER_PIXEL_THRESHOLD = int(
    os.getenv("VISUAL_PER_PIXEL_THRESHOLD", "12")
)  # pixel-level brightness threshold
BLUR_RADIUS = int(
    os.getenv("VISUAL_BLUR_RADIUS", "0")
)  # optional blur radius to reduce noise


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
    # Use the tolerant comparator with per-pixel thresholding and optional blurring
    diff_path = tmp_path / "main_window_diff.png"
    ok, ratio = compare_images(
        str(baseline),
        str(cur),
        max_diff_ratio=TOLERANCE,
        per_pixel_threshold=PER_PIXEL_THRESHOLD,
        blur_radius=BLUR_RADIUS,
        output_diff_path=str(diff_path),
    )
    w.close()
    if not ok:
        # Save debug paths in failure message to help regenerate baselines
        raise AssertionError(
            f"MainWindow visual diff too large: {ratio:.4f} > {TOLERANCE}. Diff saved to {diff_path}"
        )


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
    diff_path = tmp_path / "plot_window_diff.png"
    ok, ratio = compare_images(
        str(baseline),
        str(cur),
        max_diff_ratio=TOLERANCE,
        per_pixel_threshold=PER_PIXEL_THRESHOLD,
        blur_radius=BLUR_RADIUS,
        output_diff_path=str(diff_path),
    )
    plot.close()
    if not ok:
        raise AssertionError(
            f"PlotWindow visual diff too large: {ratio:.4f} > {TOLERANCE}. Diff saved to {diff_path}"
        )
