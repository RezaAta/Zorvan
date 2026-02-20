import json
import tempfile
from pathlib import Path

import pytest

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from zorvan.Core.CGJsonIO import load, save
from zorvan.Nodes.AbstractNode import AbstractNode
from zorvan.Nodes.CompressedNode import CompressedNode
from zorvan.Nodes.computation_type import ComputationType
from zorvan.Nodes.InitializableContainerNode import InitializableContainerNode


def test_enum_default_values():
    basic_node = InitializableContainerNode(name="W_test", value=0.5)
    assert isinstance(basic_node.computationType, ComputationType)
    assert basic_node.computationType == ComputationType.BASIC

    abs_node = AbstractNode(name="A_test", nodes=[])
    assert isinstance(abs_node.computationType, ComputationType)
    assert abs_node.computationType == ComputationType.COMPLEX

    comp_node = CompressedNode(name="C_test", nodes=[])
    assert isinstance(comp_node.computationType, ComputationType)
    assert comp_node.computationType == ComputationType.COMPLEX


def test_enum_save_load_roundtrip(tmp_path: Path):
    # Build a simple graph using Graph helper to avoid heavy dependencies
    from zorvan.Core.Graph import Graph

    graph = Graph()
    n = InitializableContainerNode(name="W_rt", value=0.1)
    graph.AddNode(n)

    f = tmp_path / "roundtrip.cgjson"
    save(graph, str(f), canvas=None, compress=False)

    # Verify file contains string value for computationType
    contents = f.read_text(encoding="utf-8")
    assert '"computationType": "basic"' in contents

    # Load back and verify attribute is converted to Enum
    g2 = load(str(f))
    loaded = next(iter(g2.nodes))
    assert isinstance(loaded.computationType, ComputationType)
    assert loaded.computationType == ComputationType.BASIC


def test_legacy_string_loads_to_enum(tmp_path: Path):
    # Craft minimal CGJSON with computationType as legacy string
    doc = {
        "metadata": {"format": "CGJSON", "version": 1},
        "nodes": [
            {
                "id": 1,
                "type": "InitializableContainerNode",
                "name": "legacy",
                "attrs": {"computationType": "basic"},
            }
        ],
        "edges": [],
        "graph": {},
    }
    p = tmp_path / "legacy.cgjson"
    p.write_text(json.dumps(doc), encoding="utf-8")

    g = load(str(p))
    n = next(iter(g.nodes))
    assert isinstance(n.computationType, ComputationType)
    assert n.computationType == ComputationType.BASIC


def test_viewmodel_exposes_string_value_for_ui():
    n = InitializableContainerNode(name="W_vm", value=0.2)
    # vm should expose a string for display
    vm = NodeEditorViewModel(n)
    vm.initialize()

    props = vm.get_properties()
    assert props.get("computationType") == "basic"
