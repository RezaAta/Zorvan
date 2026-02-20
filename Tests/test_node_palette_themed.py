import sys

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from zorvan.GUI.combined_node_palette import CombinedNodePalette
from zorvan.GUI.theme_widgets import ThemedScrollArea


def test_combined_node_palette_uses_themed_components():
    app = QApplication.instance() or QApplication([])
    palette = CombinedNodePalette()

    # Scroll area should be themed
    assert (
        isinstance(palette.scroll, ThemedScrollArea)
        or palette.scroll.property("themed") is True
    )

    # Category panels should have themed content
    panels = list(palette._category_panels.values())
    assert panels, "No category panels found in CombinedNodePalette"
    first_panel = panels[0]
    assert first_panel.content.property("themed_panel") is True

    # Node widgets should be themed and respond to theme mixin registration
    widgets = [w for w, _, _ in palette._node_widgets]
    assert widgets
    w = widgets[0]
    assert w.property("themed") is True
    # apply_theme should exist and callable
    assert hasattr(w, "apply_theme")
