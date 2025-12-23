import json
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")

from ComputationalGraphs.GUI.custom_node_manager import (
    CustomNodeDefinition,
    CustomNodeManager,
)


def test_remove_definition_persists(tmp_path):
    lib_file = tmp_path / "custom_nodes_rm.json"
    mgr = CustomNodeManager(library_path=str(lib_file))

    d = CustomNodeDefinition(
        type_name="RmNode", input_count=1, operation_code="return input1"
    )
    mgr.add_definition(d)

    # Ensure file contains the node
    data = json.loads(lib_file.read_text(encoding="utf-8"))
    types = [n.get("type_name") for n in data.get("custom_nodes", [])]
    assert "RmNode" in types

    # Remove and check file updated
    assert mgr.remove_definition("RmNode") is True
    data2 = json.loads(lib_file.read_text(encoding="utf-8"))
    types2 = [n.get("type_name") for n in data2.get("custom_nodes", [])]
    assert "RmNode" not in types2
