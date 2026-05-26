#!/usr/bin/env python
"""Run non-GUI tests by scanning the Tests/ tree and excluding files
that import PyQt6 or reference gui_framework.legacy.

Usage: python scripts/run_non_gui_tests.py
"""
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "Tests"
GUI_FRAMEWORK_DIR = ROOT / "gui_framework"

# Ensure repo root is on sys.path so imports like `zorvan` resolve
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if not TESTS_DIR.exists():
    print("Tests/ directory not found; exiting.")
    sys.exit(1)

exclude_patterns = [
    re.compile(p)
    for p in (
        r"\bPyQt6\b",
        r"gui_framework\.legacy",
        r"from\s+gui_framework\.legacy",
        r"\bgui_framework\b",
    )
]


def file_is_gui(path: pathlib.Path) -> bool:
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return True
    for pat in exclude_patterns:
        if pat.search(txt):
            return True
    return False


def collect_non_gui_tests():
    files = []
    for base in (TESTS_DIR, GUI_FRAMEWORK_DIR):
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            # skip package files and helpers
            if p.name == "__init__.py":
                continue
            # skip test files that obviously import GUI
            if file_is_gui(p):
                continue
            files.append(str(p))
    return sorted(files)


def main():
    tests = collect_non_gui_tests()
    if not tests:
        print("No non-GUI tests found.")
        return
    print(f"Running {len(tests)} non-GUI test files...")
    import pytest

    # Run pytest on the collected files
    ret = pytest.main(tests)
    raise SystemExit(ret)


if __name__ == "__main__":
    main()
