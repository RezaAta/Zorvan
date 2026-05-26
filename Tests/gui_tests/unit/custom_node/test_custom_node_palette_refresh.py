import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import (
    CombinedNodePalette,
    CustomNodeDefinition,
    get_custom_node_manager,
)


def test_combined_palette_updates_on_custom_node_add():
    app = QApplication.instance() or QApplication([])
    mgr = get_custom_node_manager()

    # Ensure test cleanliness: remove any preloaded custom nodes from the
    # default library and any leftovers from earlier tests.
    for node_type in list(mgr.get_type_names()):
        mgr.remove_definition(node_type)

    pal = CombinedNodePalette()

    # Initially there may be no Custom Nodes
    assert "Custom Nodes" not in pal._category_panels

    # Add a custom node definition
    d = CustomNodeDefinition(
        type_name="TestNodeA", input_count=1, operation_code="return input1"
    )
    mgr.add_definition(d)

    # Palette should now have a Custom Nodes panel and include TestNodeA
    assert "Custom Nodes" in pal._category_panels
    found = any(
        getattr(w, "node_type", None) == "TestNodeA"
        for w, cat, display in pal._node_widgets
    )
    assert found

    # Clean up
    mgr.remove_definition("TestNodeA")
