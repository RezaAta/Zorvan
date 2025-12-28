"""Generate UML class-diagram .drawio file for core modules (Graph, GraphProcessor, Node hierarchy).

Creates `diagrams/uml_core_modules.drawio` (overwrites if present).

Usage: python tools/generate_uml_drawio.py
"""

import base64
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "diagrams" / "uml_core_modules.drawio"
OUT.parent.mkdir(parents=True, exist_ok=True)

CELL_W = 300
CELL_H = 120

id_counter = 1


def next_id(prefix="n"):
    global id_counter
    val = f"{prefix}{id_counter}"
    id_counter += 1
    return val


def class_cell(id_, x, y, name, attrs, methods):
    # value is HTML-like; use <div> with bold class name and lists
    lines = [f"<div><b>{name}</b><hr/>"]
    for a in attrs:
        lines.append(f"- {a}<br/>")
    lines.append("<br/>")
    for m in methods:
        lines.append(f"+ {m}()<br/>")
    lines.append("</div>")
    value = "".join(lines)
    cell = ET.Element(
        "mxCell",
        {
            "id": id_,
            "value": value,
            "style": "shape=rectangle;whiteSpace=wrap;html=1;rounded=1;",
            "vertex": "1",
            "parent": "1",
        },
    )
    geom = ET.SubElement(
        cell,
        "mxGeometry",
        {
            "x": str(x),
            "y": str(y),
            "width": str(CELL_W),
            "height": str(CELL_H),
            "as": "geometry",
        },
    )
    return cell


def edge_cell(id_, source, target):
    cell = ET.Element(
        "mxCell",
        {
            "id": id_,
            "edge": "1",
            "source": source,
            "target": target,
            "parent": "1",
            "style": "endArrow=block;endFill=1;html=1;",
        },
    )
    ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    return cell


def build_model(cells):
    model = ET.Element("mxGraphModel", {"grid": "1", "gridSize": "10"})
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    for c in cells:
        root.append(c)
    return model


def compress_model_text(model_el):
    raw = ET.tostring(model_el, encoding="utf-8")
    # Use raw deflate for draw.io compatibility
    comp = zlib.compressobj(level=9, wbits=-15)
    compressed_raw = comp.compress(raw) + comp.flush()
    return base64.b64encode(compressed_raw).decode("ascii")


def make_diagram(name, cells):
    diagram = ET.Element("diagram", {"name": name, "id": name})
    model = build_model(cells)
    diagram.text = compress_model_text(model)
    return diagram


def build_graph_diagram():
    # Graph class
    g_id = next_id("n")
    g_attrs = [
        "nodes: List[Node]",
        "adjacencyMatrix: List[List[int]]",
        "idToNodeDictionary",
        "starting_nodes",
    ]
    g_methods = [
        "AddNode(*nodeObjects)",
        "ConnectPreNode(node, *preNodes)",
        "UpdateAdjacencyMatrix()",
        "RemoveNode(*identifiers)",
        "GenerateIdForNode(node)",
    ]
    g_cell = class_cell(g_id, 40, 40, "Graph", g_attrs, g_methods)

    # Optional small legend node
    return [g_cell]


def build_processor_diagram():
    p_id = next_id("n")
    p_attrs = ["graph: Graph", "max_workers", "time", "verbose", "visual"]
    p_methods = [
        "ComputeGraph(iterations, exec_options=None)",
        "ComputeGraphSingleThread(...)",
        "ForwardProcessing(...)",
        "ManualProcessing(...)",
        "mark_source_nodes_as_processed()",
        "mark_container_nodes_as_processed()",
    ]
    p_cell = class_cell(p_id, 40, 40, "GraphProcessor", p_attrs, p_methods)
    return [p_cell]


def build_node_hierarchy_diagram():
    # Node base
    n_id = next_id("n")
    n_attrs = ["predecessors", "inputs", "value", "midCalculation"]
    n_methods = [
        "Operation(*inputs)",
        "AddPreNode(*predecessors)",
        "UpdateInputs()",
        "ProcessBatch()",
    ]
    n_cell = class_cell(n_id, 40, 40, "Node", n_attrs, n_methods)

    # BasicNode
    b_id = next_id("n")
    b_attrs = ["inputCount", "computationType"]
    b_methods = ["ResetValue()", "UpdateInputs()", "IsValidInput(inp)"]
    b_cell = class_cell(b_id, 400, 40, "BasicNode", b_attrs, b_methods)

    # AbstractNode
    a_id = next_id("n")
    a_attrs = ["nodes", "computationType", "value: list"]
    a_methods = ["Operation(*inputs)", "UpdateValues()", "ProcessBatch()"]
    a_cell = class_cell(a_id, 40, 220, "AbstractNode", a_attrs, a_methods)

    # CompressedNode
    c_id = next_id("n")
    c_attrs = ["nodes", "computationType"]
    c_methods = ["Operation(*inputs)", "ProcessBatch()", "first_node/last_node"]
    c_cell = class_cell(c_id, 400, 220, "CompressedNode", c_attrs, c_methods)

    # Edges: inheritance arrows from Node to children
    e1 = edge_cell(next_id("e"), n_id, b_id)
    e2 = edge_cell(next_id("e"), n_id, a_id)
    e3 = edge_cell(next_id("e"), n_id, c_id)

    # Make inheritance style dashed and hollow arrow head
    for e in (e1, e2, e3):
        e.set("style", "dashed=1;endArrow=block;endFill=0;html=1;")

    return [n_cell, b_cell, a_cell, c_cell, e1, e2, e3]


def main():
    cells_g = build_graph_diagram()
    cells_p = build_processor_diagram()
    cells_n = build_node_hierarchy_diagram()

    mxfile = ET.Element("mxfile")
    mxfile.append(make_diagram("Graph", cells_g))
    mxfile.append(make_diagram("GraphProcessor", cells_p))
    mxfile.append(make_diagram("NodeHierarchy", cells_n))

    # Write out uncompressed top-level XML
    ET.ElementTree(mxfile).write(OUT, encoding="utf-8", xml_declaration=True)
    print("Wrote:", OUT)


if __name__ == "__main__":
    main()
