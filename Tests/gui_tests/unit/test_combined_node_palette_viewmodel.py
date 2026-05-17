from gui_framework.viewmodels.combined_node_palette_viewmodel import (
    CombinedNodePaletteViewModel,
)


def test_combined_palette_loads_categories():
    vm = CombinedNodePaletteViewModel()
    vm.initialize()
    cats = vm.get_categories()
    assert isinstance(cats, dict)
    # Expect at least one category
    assert len(cats) > 0


def test_search_text_updates():
    vm = CombinedNodePaletteViewModel()
    vm.initialize()
    vm.set_search_text("sigmoid")
    assert vm.get_search_text() == "sigmoid"
