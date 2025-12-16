from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.node_palette import NodePalette
from ComputationalGraphs.GUI.theme import get_theme_manager


def test_node_palette_updates_on_theme_change():
    app = QApplication.instance() or QApplication([])
    palette = NodePalette()
    palette.show()

    tm = get_theme_manager()

    # Ensure initial style is applied
    initial_sheet = palette.tree_widget.styleSheet() or ""

    # Change the accent and list_bg colors and ensure apply_theme updated stylesheet
    new_theme = dict(tm.theme)
    new_theme["accent"] = "#ff00ff"
    new_theme["list_bg"] = "#001122"
    tm.set_theme(new_theme, persist=False)

    # Allow signal processing
    QTest.qWait(50)

    sheet = palette.tree_widget.styleSheet()
    assert (
        "#ff00ff" in sheet or "#001122" in sheet
    ), f"Expected updated color in stylesheet, got {sheet}"

    # Cleanup: restore previous theme
    tm.set_theme(tm.load_theme(), persist=False)
    palette.close()
