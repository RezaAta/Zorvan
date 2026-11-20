from typing import Dict, List

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class CombinedNodePaletteViewModel(BaseViewModel):
    """Simple ViewModel for the Combined Node Palette.

    Loads categories from the central registry and exposes `search_text` and
    allows clients to subscribe to `on_create` and `on_select` events.
    """

    search_text = ObservableProperty("search_text", default="")

    def __init__(self):
        super().__init__()
        self._categories: Dict[str, Dict] = {}
        self._on_create_handlers = []
        self._on_select_handlers = []

    def initialize(self):
        # Load categories from registry
        try:
            from gui_framework.legacy import get_node_categories_safe

            self._categories = get_node_categories_safe()
        except Exception:
            self._categories = {}
        self._mark_initialized()

    def cleanup(self):
        # No resources to release for now
        pass

    def get_categories(self) -> Dict[str, Dict]:
        return dict(self._categories)

    def set_search_text(self, text: str):
        self.search_text = text

    def get_search_text(self) -> str:
        return str(self.search_text)

    # Event hooks
    def add_create_handler(self, fn):
        self._on_create_handlers.append(fn)

    def add_select_handler(self, fn):
        self._on_select_handlers.append(fn)

    def trigger_create(self):
        for h in list(self._on_create_handlers):
            try:
                h()
            except Exception:
                pass

    def trigger_select(self, node_type: str):
        for h in list(self._on_select_handlers):
            try:
                h(node_type)
            except Exception:
                pass
