"""Examples repository service: wraps the programmatic ExamplesLoader and exposes a simple
API for the UI to list and build examples in a testable way.
"""

from typing import Callable, Dict, Tuple

try:
    from gui_framework.examples_loader import ExamplesLoader as LegacyExamplesLoader
except Exception:  # pragma: no cover - best-effort import
    LegacyExamplesLoader = None


class ExamplesRepository:
    def __init__(self, storage_path: str = None):
        if LegacyExamplesLoader is None:
            self._loader = None
        else:
            self._loader = LegacyExamplesLoader()

        # Layout persistence file (JSON mapping example_name -> node_id -> attrs)
        import json
        import os

        self._storage_path = storage_path or os.path.join(
            os.getcwd(), ".examples_layouts.json"
        )
        # Ensure file exists
        try:
            if not os.path.exists(self._storage_path):
                with open(self._storage_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)
        except Exception:
            # If creation fails, we'll operate without persistence
            self._storage_path = None

    def list_examples(self) -> Dict[str, Tuple[Callable[[], object], str]]:
        """Return mapping example_name -> (builder_callable, description).

        If the underlying legacy loader provides categories, include all examples from all categories.
        """
        results = {}
        if self._loader is None:
            return results

        cats = getattr(self._loader, "categories", {})
        for cat in cats.values():
            for name, desc, builder in cat.examples:
                results[name] = (builder, desc)
        return results

    def list_examples_by_category(self) -> dict:
        """Return mapping category_name -> list of (name, description, builder).

        If legacy loader is not available, return one programmatic category with all examples.
        """
        results = {}
        if self._loader is None:
            # No loader available - return empty categories
            return results

        cats = getattr(self._loader, "categories", {})
        for key, cat in cats.items():
            results[cat.name] = list(cat.examples)
        # If no categories or empty, fall back to a flat category
        if not results:
            flat = [(n, d, b) for n, (b, d) in self.list_examples().items()]
            if flat:
                results["Examples"] = flat
        return results

    def build(self, name: str):
        """Call the builder for example `name` and return the built Graph (or None)."""
        examples = self.list_examples()
        if name not in examples:
            return None
        builder, _ = examples[name]
        try:
            return builder()
        except Exception:
            return None

    def save_layout(self, example_name: str, layout: dict):
        """Persist layout metadata (e.g., node_id -> {gui_pos, gui_color, gui_radius, gui_label, gui_label_color})."""
        if not self._storage_path:
            return False
        import json

        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except Exception:
            data = {}
        data[example_name] = layout
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def load_layout(self, example_name: str):
        """Load saved layout for example_name or return None if not found."""
        if not self._storage_path:
            return None
        import json

        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            return data.get(example_name)
        except Exception:
            return None
