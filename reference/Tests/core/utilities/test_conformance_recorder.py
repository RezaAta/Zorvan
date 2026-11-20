import json
from pathlib import Path

from zorvan_reference.Core.CGJsonIO import save
from zorvan_reference.Core.Graph import Graph
from zorvan_reference.Nodes.AdditionNode import AdditionNode
from zorvan_reference.Nodes.ContainerNode import ContainerNode
from tools.generate_node_conformance import NODE_TYPES
from tools.record_conformance import record_case, record_trace


def test_record_trace_captures_every_node_after_each_tick():
    graph = Graph()
    left = ContainerNode("left", 2)
    right = ContainerNode("right", 3)
    add = AdditionNode("sum")
    graph.AddNode(left, right, add)
    add.AddPreNode(left, right)
    graph.UpdateAdjacencyMatrix()

    trace = record_trace(graph, {"ticks": 2, "max_workers": 1})

    assert trace["tolerance"] == {"absolute": 1e-9, "relative": 1e-7}
    assert trace["ticks"] == [
        {"tick": 1, "values": {left.id: 2, right.id: 3, add.id: 5}},
        {"tick": 2, "values": {left.id: 2, right.id: 3, add.id: 5}},
    ]


def test_record_case_writes_portable_case_files(tmp_path):
    graph = Graph()
    source = ContainerNode("source", 4)
    graph.AddNode(source)
    graph_path = tmp_path / "source.cgjson"
    save(graph, str(graph_path))
    inputs_path = tmp_path / "inputs.json"
    inputs_path.write_text(json.dumps({"ticks": 1}), encoding="utf-8")
    output_dir = tmp_path / "conformance" / "source"

    record_case(graph_path, inputs_path, output_dir)

    assert {path.name for path in output_dir.iterdir()} == {
        "graph.json",
        "inputs.json",
        "trace.json",
    }
    trace = json.loads((output_dir / "trace.json").read_text(encoding="utf-8"))
    assert trace["ticks"] == [{"tick": 1, "values": {source.id: 4}}]


def test_seed_cases_cover_all_concrete_builtin_node_kinds():
    repository_root = Path(__file__).parents[4]
    node_cases = repository_root / "conformance" / "nodes"

    assert {node_type.__name__ for node_type in NODE_TYPES} == {
        case_dir.name for case_dir in node_cases.iterdir() if case_dir.is_dir()
    }
    for case_dir in node_cases.iterdir():
        if case_dir.is_dir():
            assert {path.name for path in case_dir.iterdir()} == {
                "graph.json",
                "inputs.json",
                "trace.json",
            }
