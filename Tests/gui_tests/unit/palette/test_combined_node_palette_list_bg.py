from PyQt6.QtWidgets import QApplication, QWidget

from gui_framework.legacy import CombinedNodePalette, get_theme_manager


def luminance(qcolor):
    # Use sRGB perceived luminance approximation
    r = qcolor.red()
    g = qcolor.green()
    b = qcolor.blue()
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def test_list_bg_is_dimmer_than_panel_bg():
    app = QApplication.instance() or QApplication([])

    class DummyPalette:
        node_categories = {"Basic Operations": {"description": "", "nodes": []}}

    parent = QWidget()
    parent.palette = DummyPalette()
    palette = CombinedNodePalette(parent)

    # Set panel_bg only (do not explicitly set list_bg) and apply theme
    from gui_framework.legacy import ColorPreferencesDialog

    dlg = ColorPreferencesDialog(parent)
    dlg.set_color_for_key("panel_bg", "#3c3f41", apply_theme=True)

    # Ensure theme applied and palette updated
    try:
        palette.apply_theme()
    except Exception:
        pass

    tb = get_theme_manager()
    panel_color = tb.get_color("panel_bg")
    list_color = palette._theme_colors.get("list_bg")

    assert list_color is not None
    # list background should be darker (lower luminance) than panel background
    assert luminance(list_color) < luminance(
        panel_color
    ), f"Expected list_bg ({list_color.name()}) to be dimmer than panel_bg ({panel_color.name()})"
