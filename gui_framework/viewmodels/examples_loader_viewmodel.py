"""
Examples loader ViewModel: lists example script files and exposes metadata
without importing them (safe for UI listing).
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

from gui_framework.viewmodels.base import BaseViewModel


class ExamplesLoaderViewModel(BaseViewModel):
    def __init__(self, search_paths: List[str] = None, repository=None):
        super().__init__()
        self.search_paths = search_paths or ["Examples", "ComputationalGraphs/Examples"]
        # Optional ExamplesRepository for programmatic examples
        self.repository = repository

    def initialize(self):
        self._mark_initialized()

    def cleanup(self):
        pass

    def list_examples(self) -> Dict[str, Tuple[str, str]]:
        """Return mapping example_name -> (absolute_path-or-name, short_description).

        If a repository is provided, prefer programmatic examples (builder functions).
        Otherwise, scan configured search paths for python example files.
        """
        results: Dict[str, Tuple[str, str]] = {}

        if self.repository is not None:
            # Repository provides builder callables and descriptions. We return the name and description.
            for name, (builder, desc) in self.repository.list_examples().items():
                results[name] = (name, desc)
            return results

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

    def list_examples_by_category(self) -> dict:
        """Return mapping category_name -> list of (name, description).

        Prefers repository categories if available; otherwise organizes filesystem examples
        under a single 'Examples' category.
        """
        if self.repository is not None:
            try:
                if hasattr(self.repository, "list_examples_by_category"):
                    cats = self.repository.list_examples_by_category()
                    # Normalize to name -> [(name, desc, builder)] -> we only need (name, desc)
                    normalized = {}
                    for cat_name, examples in cats.items():
                        normalized[cat_name] = [(n, d) for n, d, _ in examples]
                    return normalized

                # Legacy repositories only expose list_examples(); group them under
                # the traditional 'Prog' category used by the tests and older UI.
                examples = self.repository.list_examples()
                return {
                    "Prog": [(name, desc) for name, (_, desc) in examples.items()]
                }
            except Exception:
                return {}

        # Filesystem fallback
        flat = self.list_examples()
        if not flat:
            return {}
        return {"Examples": [(n, d) for n, (_, d) in flat.items()]}

    def build_example(self, name: str):
        """Build named example using the repository if available, otherwise return None.

        Returns the built object or None on failure / not found.
        """
        if self.repository is None:
            return None
        try:
            return self.repository.build(name)
        except Exception:
            return None


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
