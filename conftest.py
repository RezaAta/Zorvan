# conftest.py
# Skip test collection for any test files that import PyQt6 when PyQt6 is not installed.
import importlib
import sys
from pathlib import Path

import pytest

try:
    import PyQt6  # type: ignore

    _PYQT6_AVAILABLE = True
except Exception:
    _PYQT6_AVAILABLE = False


def pytest_ignore_collect(path, config):
    # Only check test files - path may be py.path.local, convert to pathlib.Path
    path_obj = Path(str(path))
    if path_obj.suffix != ".py":
        return False
    # pytest collection patterns include `test_*.py` and `*_test.py`.
    # Support both conventions (prefix or suffix) and also files in `Tests/`.
    if not (path_obj.name.startswith("test") or path_obj.name.endswith("_test.py")):
        return False
    # If PyQt6 installed, don't ignore
    if _PYQT6_AVAILABLE:
        return False
    # Read the file content and look for PyQt6-specific import or usage
    try:
        content = path_obj.read_text(encoding="utf-8")
    except Exception:
        return False
    # If the content references 'PyQt6' or 'QApplication', we skip collection
    if (
        "PyQt6" in content
        or "QApplication" in content
        or "from PyQt6" in content
        or "QtWidgets" in content
        or "QWidget" in content
    ):
        return True
    return False
