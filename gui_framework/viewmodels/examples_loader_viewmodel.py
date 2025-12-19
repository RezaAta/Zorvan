"""
Examples loader ViewModel: lists example script files and exposes metadata
without importing them (safe for UI listing).
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

from gui_framework.viewmodels.base import BaseViewModel


class ExamplesLoaderViewModel(BaseViewModel):
    def __init__(self, search_paths: List[str] = None):
        super().__init__()
        self.search_paths = search_paths or ["Examples", "ComputationalGraphs/Examples"]

    def initialize(self):
        self._mark_initialized()

    def cleanup(self):
        pass

    def list_examples(self) -> Dict[str, Tuple[str, str]]:
        """Return mapping example_name -> (absolute_path, short_description).

        The short_description is taken from the top-level module docstring or
        the first non-empty comment line.
        """
        results: Dict[str, Tuple[str, str]] = {}

        for sp in self.search_paths:
            p = Path(sp)
            if not p.exists():
                continue
            for child in sorted(p.iterdir()):
                if child.is_file() and child.suffix in (".py",):
                    name = child.stem
                    desc = _read_short_description(child)
                    results[name] = (str(child.resolve()), desc)

        return results


def _read_short_description(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return ""

    # First try module docstring
    import ast

    try:
        node = ast.parse(text)
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            doc = str(node.body[0].value.value).strip().splitlines()[0]
            return doc
    except Exception:
        pass

    # Fallback: first non-empty comment
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()
    return ""
