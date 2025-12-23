import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.combined_node_palette import CombinedNodePalette
from ComputationalGraphs.GUI.custom_node_manager import (
    CustomNodeDefinition,
    get_custom_node_manager,
)


def test_custom_node_delete_via_palette(monkeypatch):
    app = QApplication.instance() or QApplication([])
    mgr = get_custom_node_manager()

    # Clean up if present
    if mgr.get_definition("CtxDeleteNode"):
        mgr.remove_definition("CtxDeleteNode")

    d = CustomNodeDefinition(
        type_name="CtxDeleteNode", input_count=1, operation_code="return input1"
    )
    mgr.add_definition(d)

    pal = CombinedNodePalette()

    # Ensure node present
    assert any(
        getattr(w, "node_type", None) == "CtxDeleteNode"
        for w, c, d in pal._node_widgets
    )

    # Simulate confirmation dialog yes by patching QMessageBox.question
    from PyQt6.QtWidgets import QMessageBox

    import ComputationalGraphs.GUI.custom_node_manager as mgr_mod

    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )

    pal._delete_custom_node("CtxDeleteNode")

    assert mgr.get_definition("CtxDeleteNode") is None
    # palette should no longer contain the node
    assert not any(
        getattr(w, "node_type", None) == "CtxDeleteNode"
        for w, c, d in pal._node_widgets
    )


def test_custom_node_edit_via_palette(monkeypatch):
    app = QApplication.instance() or QApplication([])
    mgr = get_custom_node_manager()

    # Clean up if present
    if mgr.get_definition("CtxEditNode"):
        mgr.remove_definition("CtxEditNode")
    if mgr.get_definition("CtxEditNodeRenamed"):
        mgr.remove_definition("CtxEditNodeRenamed")

    d = CustomNodeDefinition(
        type_name="CtxEditNode", input_count=1, operation_code="return input1"
    )
    mgr.add_definition(d)

    pal = CombinedNodePalette()

    # Monkeypatch the CustomNodeDialog to simulate edit accept
    class StubDialog:
        def __init__(self, parent=None, existing_definition=None):
            self.definition = existing_definition

        def exec(self):
            # Simulate a rename
            new = type(self.definition)(**self.definition.to_dict())
            new.type_name = "CtxEditNodeRenamed"
            self.definition = new
            return True

    import ComputationalGraphs.GUI.custom_node_dialog as cnd

    monkeypatch.setattr(cnd, "CustomNodeDialog", StubDialog)

    pal._edit_custom_node("CtxEditNode")

    assert mgr.get_definition("CtxEditNode") is None
    assert mgr.get_definition("CtxEditNodeRenamed") is not None

    # Clean up
    mgr.remove_definition("CtxEditNodeRenamed")
