import pytest

pytest.importorskip("PyQt6")

from gui_framework.legacy import (
    CustomNodeDefinition,
    create_node,
    get_custom_node_manager,
    is_registered,
)


def test_custom_node_registered_and_creatable(tmp_path):
    mgr = get_custom_node_manager()

    # Ensure clean state
    if mgr.get_definition("QuickNode"):
        mgr.remove_definition("QuickNode")

    d = CustomNodeDefinition(
        type_name="QuickNode", input_count=1, operation_code="return input1"
    )
    mgr.add_definition(d)

    assert is_registered("QuickNode") is True

    n = create_node("QuickNode", name_hint="test")
    assert n is not None

    # cleanup
    mgr.remove_definition("QuickNode")
