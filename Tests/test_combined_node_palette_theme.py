from PyQt6.QtWidgets import QApplication, QWidget

from ComputationalGraphs.GUI.combined_node_palette import CombinedNodePalette
from ComputationalGraphs.GUI.theme import get_theme_manager


def test_palette_applies_theme_colors():
    app = QApplication.instance() or QApplication([])

    class DummyPalette:
        node_categories = {"Basic Operations": {"description": "", "nodes": []}}

    parent = QWidget()
    parent.palette = DummyPalette()
    palette = CombinedNodePalette(parent)

    # Use dialog helper to set theme colors to avoid direct signal issues
    from ComputationalGraphs.GUI.color_preferences import ColorPreferencesDialog

    dlg = ColorPreferencesDialog(parent)
    dlg.set_color_for_key("header_bg", "#112233", apply_theme=True)
    dlg.set_color_for_key("node_default", "#445566", apply_theme=True)
    dlg.set_color_for_key("node_text", "#aabbcc", apply_theme=True)
    dlg.set_color_for_key("accent", "#ff0000", apply_theme=True)

    # Ensure the palette refreshes from theme (sometimes timing differs in tests)
    try:
        palette.apply_theme()
    except Exception:
        pass

    # After theme set, palette should have cached theme colors
    assert palette._theme_colors["header_bg"] == "#112233"
    # Header stylesheet should include the header color
    panel = palette._category_panels.get("Basic Operations")
    assert panel is not None
    assert "#112233" in panel.header.styleSheet()

    # Node widgets should repaint without error
    # (Create a sample node widget to validate colors are used)
    palette._category_panels = {
        "Basic Operations": palette._category_panels.get("Basic Operations")
    }
    # Add a node for repaint check
    from ComputationalGraphs.GUI.combined_node_palette import NodeItemWidget

    w = NodeItemWidget("AdditionNode", "Addition", "Adds values", palette)
    palette._node_widgets.append((w, "Basic Operations", "addition"))
    w.repaint()
    app.processEvents()
    assert palette._theme_colors["node_text"].name() == "#aabbcc"
