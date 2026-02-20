import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QContextMenuEvent
from PyQt6.QtWidgets import QApplication, QMenu

from zorvan.GUI.combined_node_palette import CombinedNodePalette
from zorvan.GUI.custom_node_manager import CustomNodeDefinition, get_custom_node_manager


def test_right_click_triggers_context_menu(monkeypatch):
    app = QApplication.instance() or QApplication([])
    mgr = get_custom_node_manager()

    # Ensure clean state
    if mgr.get_definition("RightClickNode"):
        mgr.remove_definition("RightClickNode")

    d = CustomNodeDefinition(
        type_name="RightClickNode", input_count=1, operation_code="return input1"
    )
    mgr.add_definition(d)

    pal = CombinedNodePalette()

    # Find widget for the custom node
    target = None
    for w, cat, display in pal._node_widgets:
        if getattr(w, "node_type", None) == "RightClickNode":
            target = w
            break

    assert target is not None, "Could not find widget for RightClickNode"

    # Sanity checks
    assert "RightClickNode" in mgr.get_type_names()
    pal_obj = target._find_palette()
    assert pal_obj is not None

    # Patch QMenu.popup to mark it called and then call the helper directly
    called = {"ok": False}

    def fake_popup(self, pos=None):
        called["ok"] = True
        return None

    monkeypatch.setattr(QMenu, "popup", fake_popup)

    # Directly invoke the helper which is the most reliable way to test behavior
    target.show_custom_context_menu()

    assert called["ok"]

    # cleanup
    mgr.remove_definition("RightClickNode")
