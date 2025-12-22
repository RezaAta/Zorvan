"""Adapter exposing MVVM CombinedNodePaletteView under legacy API.

This adapter constructs a `CombinedNodePaletteViewModel` and uses the MVVM
wrapper view to host the existing legacy widget while providing a stable
API for the rest of the application.
"""

try:
    from gui_framework.viewmodels.combined_node_palette_viewmodel import (
        CombinedNodePaletteViewModel,
    )
    from gui_framework.views.combined_node_palette_view import CombinedNodePaletteView
except Exception as e:
    raise ImportError("CombinedNodePalette MVVM components unavailable: " + str(e))


class CombinedNodePaletteAdapter:
    def __init__(self, parent=None):
        self._vm = CombinedNodePaletteViewModel()
        try:
            self._vm.initialize()
        except Exception:
            pass
        self._view = CombinedNodePaletteView(self._vm, parent)

    def widget(self):
        return self._view.widget()

    def add_create_handler(self, fn):
        return self._vm.add_create_handler(fn)

    def add_select_handler(self, fn):
        return self._vm.add_select_handler(fn)

    def set_search_text(self, t):
        return self._vm.set_search_text(t)

    def get_categories(self):
        return self._vm.get_categories()

    def close(self):
        try:
            w = self.widget()
            w.close()
        except Exception:
            pass

    def __getattr__(self, name):
        # Delegate to underlying view/palette for any other attribute
        try:
            return getattr(self.widget(), name)
        except Exception:
            raise AttributeError(name)
