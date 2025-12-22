"""ViewModel for ReplaceNode dialog: provides node categories and filtering."""

from typing import Dict, List, Tuple

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class ReplaceNodeViewModel(BaseViewModel):
    """Manages node categories and search/filter logic."""

    search_text = ObservableProperty("search_text", default="")
    categories_changed = ObservableProperty("categories_changed", default=0)

    def __init__(self, node_categories: Dict[str, Dict] = None):
        super().__init__()
        # node_categories expected to be mapping category -> {description, nodes: [(type, display, desc), ...]}
        self._node_categories = node_categories or {}
        self._filtered = []  # list of tuples (category, node) flattened
        self._last_search = ""
        self.create_filtered_list("")

    def initialize(self):
        self._mark_initialized()

    def cleanup(self):
        pass

    def set_search_text(self, text: str):
        if text != self.search_text:
            self.search_text = text
            self.create_filtered_list(text)

    def get_search_text(self) -> str:
        return self.search_text

    def create_filtered_list(self, text: str):
        t = (text or "").lower()
        self._filtered = []
        for category, data in self._node_categories.items():
            for n in data.get("nodes", []):
                type_name = n[0]
                display = n[1]
                desc = n[2] if len(n) > 2 else ""
                if (
                    not t
                    or t in display.lower()
                    or t in type_name.lower()
                    or t in desc.lower()
                ):
                    self._filtered.append((category, type_name, display, desc))
        self.categories_changed += 1

    def get_filtered(self) -> List[Tuple[str, str, str, str]]:
        return list(self._filtered)

    def load_from_registry(self, registry_getter):
        try:
            self._node_categories = registry_getter()
            self.create_filtered_list(self.search_text)
            return True
        except Exception:
            return False

    def select_type(self, type_name: str) -> bool:
        # Return True if type exists in categories
        for _, t, _, _ in self._filtered:
            if t == type_name:
                return True
        return False
