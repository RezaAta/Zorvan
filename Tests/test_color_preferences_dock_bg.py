from PyQt6.QtWidgets import QApplication, QWidget

from ComputationalGraphs.GUI.color_preferences import ColorPreferencesDialog
from ComputationalGraphs.GUI.combined_node_palette import CombinedNodePalette


def test_dock_bg_preference_updates_palette_body():
    app = QApplication.instance() or QApplication([])

    parent = QWidget()

    class DummyPalette:
        node_categories = {"Basic Operations": {"description": "", "nodes": []}}

    parent.palette = DummyPalette()
    palette = CombinedNodePalette(parent)

    dlg = ColorPreferencesDialog(parent)
    # Set the single authoritative panel background and apply
    dlg.set_color_for_key("panel_bg", "#0a0b0c", apply_theme=True)

    # Ensure palette refreshed
    try:
        palette.apply_theme()
    except Exception:
        pass

    # The theme cache should include dock_bg derived from panel_bg
    assert palette._theme_colors.get("dock_bg").name() == "#0a0b0c"

    # The main widget (internal) should have style updated to include the color
    main_widget = palette.widget()
    assert main_widget is not None
    assert "#0a0b0c" in main_widget.styleSheet()
