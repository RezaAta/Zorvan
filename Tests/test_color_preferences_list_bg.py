from PyQt6.QtWidgets import QApplication, QWidget

from ComputationalGraphs.GUI.color_preferences import ColorPreferencesDialog
from ComputationalGraphs.GUI.combined_node_palette import CombinedNodePalette
from ComputationalGraphs.GUI.theme import get_theme_manager


def test_list_bg_preference_updates_palette():
    app = QApplication.instance() or QApplication([])

    # Setup parent and palette
    parent = QWidget()

    class DummyPalette:
        node_categories = {"Basic Operations": {"description": "", "nodes": []}}

    parent.palette = DummyPalette()

    palette = CombinedNodePalette(parent)

    # Open preferences dialog and set panel_bg programmatically (authoritative key)
    dlg = ColorPreferencesDialog(parent)
    dlg.set_color_for_key("panel_bg", "#123456", apply_theme=True)

    tm = get_theme_manager()
    # theme manager should have panel_bg applied
    assert tm.theme.get("panel_bg") == "#123456"

    # Ensure palette refreshed
    try:
        palette.apply_theme()
    except Exception:
        pass

    # Palette cached colors should include list_bg derived from panel_bg
    list_bg = tm.get_color("list_bg").name()
    panel_bg = tm.get_color("panel_bg").name()
    from PyQt6.QtGui import QColor

    if list_bg == panel_bg:
        expected = QColor(panel_bg).darker(108).name()
    else:
        expected = list_bg
    assert palette._theme_colors.get("list_bg").name() == expected

    # Also ensure content stylesheet contains the expected color string (visual effect)
    panel = palette._category_panels.get("Basic Operations")
    assert panel is not None
    assert expected in panel.content.styleSheet()
