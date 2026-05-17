import importlib.util
from pathlib import Path

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

# Find screenshot utility (tests utils)
screenshot_path = None
for parent in Path(__file__).resolve().parents:
    candidate = parent / ".." / "Tests" / "utils" / "screenshot.py"
    if candidate.exists():
        screenshot_path = candidate.resolve()
        break
if screenshot_path is None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "Tests" / "utils" / "screenshot.py"
        if candidate.exists():
            screenshot_path = candidate.resolve()
            break

if screenshot_path is None:
    raise FileNotFoundError("Could not find Tests/utils/screenshot.py")

spec = importlib.util.spec_from_file_location("screenshot_utils", str(screenshot_path))
screenshot_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screenshot_utils)
capture_widget_to_file = screenshot_utils.capture_widget_to_file
PIL_AVAILABLE = getattr(screenshot_utils, "PIL_AVAILABLE", False)

import pytest

from gui_framework.viewmodels.examples_loader_viewmodel import ExamplesLoaderViewModel
from gui_framework.views.examples_loader_view import ExamplesLoaderView

pytestmark = pytest.mark.skipif(
    not (PYQT and PIL_AVAILABLE), reason="PyQt6 and Pillow required"
)


def test_examples_loader_view_screenshot(qtbot, tmp_path):
    repo = type(
        "R",
        (),
        {
            "list_examples_by_category": lambda self: {
                "Prog": [("ex1", "Example 1"), ("ex2", "Example 2")]
            },
            "list_examples": lambda self: {"ex1": (lambda: None, "Example 1")},
        },
    )()
    vm = ExamplesLoaderViewModel(repository=repo)
    view = ExamplesLoaderView(vm)
    qtbot.addWidget(view)
    view.show()

    # capture screenshot
    out = tmp_path / "examples_view.png"
    p = capture_widget_to_file(view, str(out))
    assert p.exists()
    # Ensure PIL can open it
    from PIL import Image

    img = Image.open(str(p))
    assert img is not None
