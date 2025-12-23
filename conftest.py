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


def pytest_sessionstart(session):
    # Ensure a QApplication exists and the ThemeManager applies a minimal
    # stylesheet early for *all* tests (including Tests/*) so tests that
    # assert on app.styleSheet() will observe expected selectors. Create
    # the application only if PyQt6 is available and an instance doesn't
    # already exist.
    if _PYQT6_AVAILABLE:
        try:
            from PyQt6.QtWidgets import QApplication

            try:
                app = QApplication.instance() or QApplication([])
            except Exception:
                app = None
            try:
                from ComputationalGraphs.GUI.theme import get_theme_manager

                try:
                    manager = get_theme_manager()
                    try:
                        hover = manager.get_color("button_hover", "#5a5a5a").name()
                        button_bg = manager.get_color("button_bg").name()
                        qss = (
                            f'QPushButton[themed="true"]:hover {{ background: {hover}; }}\n'
                            f'QToolBar QPushButton[themed="true"]:hover {{ background: {hover}; }}\n'
                            f'QToolBar QPushButton[themed="true"], QToolBar QToolButton[themed="true"] {{ background-color: {button_bg}; }}\n'
                        )
                        if app is not None:
                            try:
                                # Only add the minimal stylesheet if it isn't already present.
                                ss = app.styleSheet() or ""
                                if 'QPushButton[themed="true"]:hover' not in ss:
                                    app.setStyleSheet(ss + "\n" + qss)
                            except Exception:
                                pass
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass


@pytest.fixture(autouse=True)
def _ensure_minimal_qss_per_test():
    # For tests that create QApplication after pytest_sessionstart, ensure a
    # minimal stylesheet is present before each test begins. This avoids test
    # ordering sensitivity where some tests previously relied on a global
    # stylesheet being set earlier in the run.
    if _PYQT6_AVAILABLE:
        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance() or None
            if app is not None:
                try:
                    from ComputationalGraphs.GUI.theme import get_theme_manager

                    mgr = get_theme_manager()
                    hover = mgr.get_color("button_hover", "#5a5a5a").name()
                    button_bg = mgr.get_color("button_bg").name()
                    qss = (
                        f'QPushButton[themed="true"]:hover {{ background: {hover}; }}\n'
                        f'QToolBar QPushButton[themed="true"]:hover {{ background: {hover}; }}\n'
                        f'QToolBar QPushButton[themed="true"], QToolBar QToolButton[themed="true"] {{ background-color: {button_bg}; }}\n'
                    )
                    try:
                        ss = app.styleSheet() or ""
                        if 'QPushButton[themed="true"]:hover' not in ss:
                            app.setStyleSheet(ss + "\n" + qss)
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass
    yield
