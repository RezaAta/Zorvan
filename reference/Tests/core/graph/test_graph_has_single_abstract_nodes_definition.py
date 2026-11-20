import ast
from pathlib import Path


def test_graph_defines_abstract_nodes_once():
    graph_path = Path(__file__).parents[3] / "zorvan_reference" / "Core" / "Graph.py"
    module = ast.parse(graph_path.read_text(encoding="utf-8"))
    graph_class = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "Graph"
    )

    definitions = [
        node
        for node in graph_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "AbstractNodes"
    ]

    assert len(definitions) == 1
