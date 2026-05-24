from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import CombinedNodePalette
from gui_framework.legacy import get_theme_manager


def test_combined_palette_updates_on_theme_change():
    app = QApplication.instance() or QApplication([])
    palette = CombinedNodePalette()
    palette.show()

    tm = get_theme_manager()

    # Change the accent and list_bg colors and ensure apply_theme updated stylesheet
    new_theme = dict(tm.theme)
    new_theme["accent"] = "#ff00ff"
    new_theme["list_bg"] = "#001122"
    tm.set_theme(new_theme, persist=False)

    # Allow signal processing
    QTest.qWait(50)
    app = QApplication.instance()
    if app is not None:
        app.processEvents()

    # Ensure the combined palette applied the theme - inspect first category panel content
    try:
        # There should be at least one category panel populated
        panels = list(palette._category_panels.values())
        assert panels, "No category panels found in CombinedNodePalette"
        content = panels[0].content
        sheet = content.styleSheet() or ""
    except Exception:
        # If something goes wrong, try to force-apply theme
        try:
            palette.apply_theme()
        except Exception:
            pass
        sheet = ""

    # The palette may derive a slightly darker list_bg when it matches panel_bg.
    list_bg = tm.get_color("list_bg").name()
    panel_bg = tm.get_color("panel_bg").name()
    from PyQt6.QtGui import QColor

    if list_bg == panel_bg:
        expected = QColor(panel_bg).darker(108).name()
    else:
        expected = list_bg

    assert (
        expected in sheet
    ), f"Expected updated color {expected} in panel stylesheet, got {sheet}"

    # Cleanup: restore previous theme
    tm.set_theme(tm.load_theme(), persist=False)
    palette.close()
