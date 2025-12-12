import inspect
import json
import os
import zipfile
from typing import Any, Dict

import numpy as np

from ComputationalGraphs.Core.Graph import Graph


def _is_primitive(o):
    return isinstance(o, (int, float, bool, str, type(None)))


def _serialize_value(v):
    # Primitive types
    if _is_primitive(v):
        return v
    # Numpy arrays
    if isinstance(v, np.ndarray):
        return {
            "__type__": "ndarray",
            "dtype": str(v.dtype),
            "shape": v.shape,
            "data": v.tolist(),
        }
    # Lists / tuples
    if isinstance(v, (list, tuple)):
        return [_serialize_value(x) for x in v]
    # Dicts
    if isinstance(v, dict):
        return {str(k): _serialize_value(val) for k, val in v.items()}
    # Fallback: use repr as string
    try:
        return repr(v)
    except Exception:
        return str(v)


def _deserialize_value(v):
    if isinstance(v, dict) and v.get("__type__") == "ndarray":
        data = np.array(v.get("data", []), dtype=v.get("dtype", float))
        # reshape to the intended shape if provided
        sh = tuple(v.get("shape", ()))
        if sh:
            try:
                data = data.reshape(sh)
            except Exception:
                pass
        return data
    if isinstance(v, list):
        return [_deserialize_value(x) for x in v]
    if isinstance(v, dict):
        return {k: _deserialize_value(x) for k, x in v.items()}
    return v


def _get_node_attributes(node):
    attrs = {}
    for name, val in vars(node).items():
        if name.startswith("_"):
            continue
        if name in ("predecessors", "inputs", "listOfNodes"):
            continue
        if inspect.isroutine(val):
            continue
        attrs[name] = val
    return attrs


def _serialize_internal_node(node):
    """Serialize a node that's internal to a CompressedNode."""
    attrs = _get_node_attributes(node)
    attrs_serialized = {}
    for k, v in attrs.items():
        try:
            attrs_serialized[k] = _serialize_value(v)
        except Exception:
            continue

    return {
        "id": getattr(node, "id", None),
        "type": type(node).__name__,
        "name": getattr(node, "name", None),
        "attrs": attrs_serialized,
        # Store predecessor IDs for internal connections
        "predecessor_ids": [
            getattr(p, "id", None) for p in getattr(node, "predecessors", [])
        ],
    }


def save(graph: Graph, filename: str, canvas=None, compress=True):
    """Serialize a Graph to JSON (optionally zipped) and store visuals if canvas is provided.

    The output format can be:
    - `.cgjson` (plain JSON)
    - `.cgz` (zip with graph.json)
    - `.json` (plain JSON)

    Custom nodes are embedded in the file for portability.
    """
    doc = {
        "metadata": {"format": "CGJSON", "version": 1},
        "nodes": [],
        "edges": [],
        "graph": {},
        "custom_nodes": [],  # For embedding custom node definitions
    }

    # Collect custom node definitions used in this graph
    custom_nodes_used = set()
    for node in graph.nodes:
        node_type = type(node).__name__
        if hasattr(node, "_is_custom_node") and node._is_custom_node:
            custom_nodes_used.add(node_type)

    # If custom nodes are used, embed their definitions
    if custom_nodes_used:
        try:
            from ComputationalGraphs.GUI.custom_node_manager import (
                get_custom_node_manager,
            )

            manager = get_custom_node_manager()
            for type_name in custom_nodes_used:
                definition = manager.get_definition(type_name)
                if definition:
                    doc["custom_nodes"].append(definition.to_dict())
        except Exception:
            # If custom node manager unavailable, continue without embedding
            pass

    # Node list
    for node in graph.nodes:
        attrs = _get_node_attributes(node)
        # Serialize attr values
        attrs_serialized = {}
        for k, v in attrs.items():
            try:
                attrs_serialized[k] = _serialize_value(v)
            except Exception:
                # Skip non-serializable attributes
                continue

        node_entry = {
            "id": getattr(node, "id", None),
            "type": type(node).__name__,
            "name": getattr(node, "name", None),
            "attrs": attrs_serialized,
        }

        # Special handling for CompressedNode - serialize internal nodes
        if type(node).__name__ == "CompressedNode":
            internal_nodes = getattr(node, "listOfNodes", [])
            node_entry["internal_nodes"] = [
                _serialize_internal_node(n) for n in internal_nodes
            ]

        # Special handling for AbstractNode - serialize internal nodes
        if type(node).__name__ == "AbstractNode":
            internal_nodes = getattr(node, "listOfNodes", [])
            node_entry["internal_nodes"] = [
                _serialize_internal_node(n) for n in internal_nodes
            ]

        # Add visuals from canvas if provided
        if (
            canvas is not None
            and hasattr(canvas, "node_items")
            and node in canvas.node_items
        ):
            item = canvas.node_items[node]
            pos = item.pos()
            color = None
            try:
                color = (
                    item.color.name()
                    if getattr(item, "color", None) is not None
                    else None
                )
            except Exception:
                color = None
            node_entry["visuals"] = {
                "x": pos.x(),
                "y": pos.y(),
                "radius": getattr(item, "radius", None),
                "color": color,
                "label": item.label.toPlainText() if hasattr(item, "label") else None,
            }

        doc["nodes"].append(node_entry)

    # Edges (predecessors mapping)
    for node in graph.nodes:
        if hasattr(node, "predecessors") and node.predecessors:
            for pred in node.predecessors:
                doc["edges"].append(
                    {
                        "source": getattr(pred, "id", None),
                        "target": getattr(node, "id", None),
                    }
                )

    # Graph-level properties: starting_nodes, stopping_nodes, manual_processing_sequence
    try:
        doc["graph"]["starting_nodes"] = [
            getattr(n, "id", None) for n in getattr(graph, "starting_nodes", [])
        ]
    except Exception:
        doc["graph"]["starting_nodes"] = []
    try:
        doc["graph"]["stopping_nodes"] = [
            getattr(n, "id", None) for n in getattr(graph, "stopping_nodes", [])
        ]
    except Exception:
        doc["graph"]["stopping_nodes"] = []
    try:
        # manual seq: convert node objects to ids
        manual = getattr(graph, "manual_processing_sequence", None)
        if manual:
            doc["graph"]["manual_processing_sequence"] = [
                [getattr(n, "id", None) for n in step] for step in manual
            ]
        else:
            doc["graph"]["manual_processing_sequence"] = None
    except Exception:
        doc["graph"]["manual_processing_sequence"] = None

    # === Multi-Graph Support: Save graph identity and sub-graphs ===
    try:
        doc["graph"]["graph_id"] = getattr(graph, "graph_id", None)
        doc["graph"]["graph_name"] = getattr(graph, "graph_name", "Default Graph")
        doc["graph"]["graph_color"] = getattr(graph, "graph_color", "#4ECDC4")
        doc["graph"]["is_mother_graph"] = getattr(graph, "is_mother_graph", True)

        # Serialize sub-graphs
        sub_graphs = getattr(graph, "sub_graphs", [])
        if sub_graphs:
            doc["graph"]["sub_graphs"] = [
                sg.get_subgraph_metadata() for sg in sub_graphs
            ]
        else:
            doc["graph"]["sub_graphs"] = []
    except Exception:
        doc["graph"]["sub_graphs"] = []

    # Dump to file
    fname = filename
    root, ext = os.path.splitext(fname)
    if ext.lower() in (".cgz", ".zip") and compress:
        # Write JSON and compress
        with zipfile.ZipFile(fname, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("graph.json", json.dumps(doc, default=str, indent=2))
    else:
        # Dump plain JSON
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, default=str)


def _find_node_class(typename: str):
    # First try custom nodes
    try:
        from ComputationalGraphs.GUI.custom_node_manager import get_custom_node_manager

        manager = get_custom_node_manager()
        custom_class = manager.get_node_class(typename)
        if custom_class:
            return custom_class
    except Exception:
        pass

    # Attempt to locate the node class by name in ComputationalGraphs.Nodes
    try:
        import ComputationalGraphs.Nodes as NodesPkg

        for name, obj in inspect.getmembers(NodesPkg):
            if name == typename and inspect.isclass(obj):
                return obj
    except Exception:
        pass
    # Fallback to search modules
    try:
        import ComputationalGraphs.Nodes as NodesPkg

        for name, obj in inspect.getmembers(NodesPkg):
            if inspect.isclass(obj) and obj.__name__ == typename:
                return obj
    except Exception:
        pass
    return None


def load(filename: str) -> Graph:
    # Read file (.cgz zipped or .cgjson)
    root, ext = os.path.splitext(filename)
    if ext.lower() in (".cgz", ".zip"):
        with zipfile.ZipFile(filename, "r") as zf:
            data = zf.read("graph.json").decode("utf-8")
    else:
        with open(filename, "r", encoding="utf-8") as f:
            data = f.read()

    doc = json.loads(data)
    graph = Graph()
    id_map = {}

    # Handle embedded custom nodes - recreate them from definitions
    custom_nodes_data = doc.get("custom_nodes", [])
    if custom_nodes_data:
        try:
            from ComputationalGraphs.GUI.custom_node_manager import (
                CustomNodeDefinition,
                get_custom_node_manager,
            )

            manager = get_custom_node_manager()
            for definition_dict in custom_nodes_data:
                try:
                    definition = CustomNodeDefinition.from_dict(definition_dict)
                    # Add to manager (regenerate class if needed)
                    manager.add_definition(definition)
                except Exception as e:
                    print(
                        f"Warning: Failed to load custom node {definition_dict.get('type_name', 'unknown')}: {e}"
                    )
        except Exception as e:
            print(f"Warning: Could not load custom node definitions: {e}")

    # Create nodes
    for n in doc.get("nodes", []):
        ntype = n.get("type", "DisplayNode")
        name = n.get("name", None)
        cls = _find_node_class(ntype)
        try:
            # If class accepts name param, attempt to construct accordingly
            if cls is not None:
                node = (
                    cls(name=name)
                    if "name" in inspect.signature(cls.__init__).parameters
                    else cls()
                )
            else:
                # Fallback to DisplayNode
                from ComputationalGraphs.Nodes.DisplayNode import DisplayNode

                node = DisplayNode(name=name)
        except Exception:
            try:
                from ComputationalGraphs.Nodes.DisplayNode import DisplayNode

                node = DisplayNode(name=name)
            except Exception:
                raise

        # set attrs
        attrs = n.get("attrs", {})
        for ak, av in attrs.items():
            try:
                parsed_val = _deserialize_value(av)
                setattr(node, ak, parsed_val)
            except Exception:
                # skip non-settable attributes
                continue

        # Special handling for CompressedNode - reconstruct internal nodes
        if ntype == "CompressedNode" and "internal_nodes" in n:
            internal_node_data = n.get("internal_nodes", [])
            internal_nodes = []
            internal_id_map = {}

            # First pass: create all internal nodes
            for int_n in internal_node_data:
                int_cls = _find_node_class(int_n.get("type", "DisplayNode"))
                int_name = int_n.get("name", None)
                try:
                    if int_cls is not None:
                        sig = inspect.signature(int_cls.__init__)
                        int_node = (
                            int_cls(name=int_name)
                            if "name" in sig.parameters
                            else int_cls()
                        )
                    else:
                        from ComputationalGraphs.Nodes.DisplayNode import DisplayNode

                        int_node = DisplayNode(name=int_name)
                except Exception:
                    from ComputationalGraphs.Nodes.DisplayNode import DisplayNode

                    int_node = DisplayNode(name=int_name)

                # Set attributes
                for ak, av in int_n.get("attrs", {}).items():
                    try:
                        setattr(int_node, ak, _deserialize_value(av))
                    except Exception:
                        continue

                int_node.id = int_n.get("id", None)
                internal_nodes.append(int_node)
                internal_id_map[int_node.id] = int_node

            # Second pass: connect internal predecessors
            for i, int_n in enumerate(internal_node_data):
                pred_ids = int_n.get("predecessor_ids", [])
                for pid in pred_ids:
                    pred = internal_id_map.get(pid) or id_map.get(pid)
                    if pred is not None:
                        internal_nodes[i].AddPreNode(pred)

            # Set the internal nodes on the CompressedNode
            node.listOfNodes = internal_nodes

            # Also add internal nodes to id_map so edges can reference them
            for int_node in internal_nodes:
                if int_node.id:
                    id_map[int_node.id] = int_node

        # Special handling for AbstractNode - reconstruct internal nodes
        if ntype == "AbstractNode" and "internal_nodes" in n:
            internal_node_data = n.get("internal_nodes", [])
            internal_nodes = []
            internal_id_map = {}

            # First pass: create all internal nodes
            for int_n in internal_node_data:
                int_cls = _find_node_class(int_n.get("type", "DisplayNode"))
                int_name = int_n.get("name", None)
                try:
                    if int_cls is not None:
                        sig = inspect.signature(int_cls.__init__)
                        int_node = (
                            int_cls(name=int_name)
                            if "name" in sig.parameters
                            else int_cls()
                        )
                    else:
                        from ComputationalGraphs.Nodes.DisplayNode import DisplayNode

                        int_node = DisplayNode(name=int_name)
                except Exception:
                    from ComputationalGraphs.Nodes.DisplayNode import DisplayNode

                    int_node = DisplayNode(name=int_name)

                # Set attributes
                for ak, av in int_n.get("attrs", {}).items():
                    try:
                        setattr(int_node, ak, _deserialize_value(av))
                    except Exception:
                        continue

                int_node.id = int_n.get("id", None)
                internal_nodes.append(int_node)
                internal_id_map[int_node.id] = int_node

            # Second pass: connect internal predecessors (AbstractNode nodes are
            # disjoint, so internal predecessor connections should be empty, but
            # we handle this for robustness in case of nested nodes)
            for i, int_n in enumerate(internal_node_data):
                pred_ids = int_n.get("predecessor_ids", [])
                for pid in pred_ids:
                    pred = internal_id_map.get(pid) or id_map.get(pid)
                    if pred is not None:
                        internal_nodes[i].AddPreNode(pred)

            # Set the internal nodes on the AbstractNode
            node.listOfNodes = internal_nodes

            # Also add internal nodes to id_map so edges can reference them
            for int_node in internal_nodes:
                if int_node.id:
                    id_map[int_node.id] = int_node

        # Convert some typed attributes to preferred types (e.g., tuple for gui_pos)
        if hasattr(node, "gui_pos") and isinstance(getattr(node, "gui_pos"), list):
            try:
                node.gui_pos = tuple(node.gui_pos)
            except Exception:
                pass

        # Set id to match original
        nid = n.get("id", None)
        node.id = nid

        # Store visuals (as temporary attributes) if present
        vis = n.get("visuals", {})
        if vis:
            try:
                node.gui_pos = (float(vis.get("x", 0.0)), float(vis.get("y", 0.0)))
            except Exception:
                node.gui_pos = None
            node.gui_color = vis.get("color", None)
            try:
                node.gui_radius = (
                    float(vis.get("radius")) if vis.get("radius") is not None else None
                )
            except Exception:
                node.gui_radius = None
            node.gui_label = vis.get("label", None)

        graph.AddNode(node)
        id_map[nid] = node

    # Connect edges
    for e in doc.get("edges", []):
        src = id_map.get(e.get("source"))
        tgt = id_map.get(e.get("target"))
        if src is not None and tgt is not None:
            tgt.AddPreNode(src)

    # Graph-level properties
    try:
        starting_ids = doc.get("graph", {}).get("starting_nodes", [])
        graph.starting_nodes = [id_map.get(i) for i in starting_ids if i in id_map]
    except Exception:
        pass
    try:
        stopping_ids = doc.get("graph", {}).get("stopping_nodes", [])
        graph.stopping_nodes = [id_map.get(i) for i in stopping_ids if i in id_map]
    except Exception:
        pass
    try:
        manual_seq = doc.get("graph", {}).get("manual_processing_sequence")
        if manual_seq:
            graph.manual_processing_sequence = [
                [id_map.get(i) for i in step if i in id_map] for step in manual_seq
            ]
    except Exception:
        pass

    # === Multi-Graph Support: Restore sub-graphs ===
    try:
        graph_meta = doc.get("graph", {})

        # Restore graph identity
        graph.graph_id = graph_meta.get("graph_id", graph.graph_id)
        graph.graph_name = graph_meta.get("graph_name", graph.graph_name)
        graph.graph_color = graph_meta.get("graph_color", graph.graph_color)
        graph.is_mother_graph = graph_meta.get("is_mother_graph", True)

        # Restore sub-graphs
        sub_graphs_data = graph_meta.get("sub_graphs", [])
        for sg_meta in sub_graphs_data:
            graph.restore_subgraph_from_metadata(sg_meta, id_map)
    except Exception:
        # If sub-graph restoration fails, continue without them
        pass

    # Update adjacency matrix
    graph.UpdateAdjacencyMatrix()
    return graph
