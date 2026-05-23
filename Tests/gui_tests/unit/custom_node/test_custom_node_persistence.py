import json
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")

from zorvan.GUI.custom_node_manager import CustomNodeDefinition, CustomNodeManager


def test_add_definition_persists_to_library(tmp_path):
    lib_file = tmp_path / "custom_nodes_test.json"
    mgr = CustomNodeManager(library_path=str(lib_file))

    # Ensure no file initially
    assert not lib_file.exists()

    d = CustomNodeDefinition(
        type_name="PersistNode", input_count=1, operation_code="return input1"
    )
    assert mgr.add_definition(d) is True

    # Now file should exist and include the definition
    assert lib_file.exists()
    data = json.loads(lib_file.read_text(encoding="utf-8"))
    types = [n.get("type_name") for n in data.get("custom_nodes", [])]
    assert "PersistNode" in types

    # Clean up
    mgr.remove_definition("PersistNode")
    assert not mgr.get_definition("PersistNode")


def test_load_library_reads_definitions(tmp_path):
    lib_file = tmp_path / "custom_nodes_test2.json"
    data = {
        "version": 1,
        "custom_nodes": [
            {
                "type_name": "LoadedNode",
                "input_count": 1,
                "operation_code": "return input1",
                "custom_properties": [],
            }
        ],
    }
    lib_file.write_text(json.dumps(data), encoding="utf-8")

    mgr = CustomNodeManager(library_path=str(lib_file))
    assert mgr.load_library() is True
    assert mgr.get_definition("LoadedNode") is not None
    # cleanup
    mgr.remove_definition("LoadedNode")
