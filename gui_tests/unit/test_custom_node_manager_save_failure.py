import pytest

pytest.importorskip("PyQt6")

from ComputationalGraphs.GUI.custom_node_manager import (
    CustomNodeDefinition,
    CustomNodeManager,
)


def test_add_definition_raises_if_save_fails(monkeypatch, tmp_path):
    lib_file = tmp_path / "custom_nodes_fail.json"
    mgr = CustomNodeManager(library_path=str(lib_file))

    # Force save_library to return False
    monkeypatch.setattr(mgr, "save_library", lambda: False)

    d = CustomNodeDefinition(
        type_name="FailNode", input_count=1, operation_code="return input1"
    )
    with pytest.raises(Exception):
        mgr.add_definition(d)
