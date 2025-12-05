import inspect
import subprocess
import xml.etree.ElementTree as ET

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes import *

# Map draw.io node_type attribute to Python classes
NODE_TYPE_MAP = {
    "Addition": AdditionNode,
    "DataStream": DataStreamNode,
    "Display": DisplayNode,
    "Abstract": AbstractNode,
    "Compressed": CompressedNode,
    "Container": ContainerNode,
    "Linear": LinearNode,
    "LinearDerivative": LinearNodeDerivative,
    "MeanSquared": MeanSquaredNode,
    "Multiplication": MultiplicationNode,
    "ReLU": ReLUNode,
    "Sigmoid": SigmoidNode,
    "SigmoidDerivative": SigmoidDerivativeNode,
    "Tanh": TanhNode,
    "TanhDerivative": TanhDerivativeNode,
    "Subtraction": SubtractionNode,
    "PiecewiseLinear": PiecewiseLinearNode,
    "Min": MinNode,
    "Max": MaxNode,
    "Gaussian": GaussianNode,
    "Division": DivisionNode,
}


def get_node_attributes(node):
    """
    Introspect a node and return its non-callable, non-private attributes,
    excluding 'predecessors' and 'inputs'.
    """
    attrs = {}
    for name, val in vars(node).items():
        if (
            not name.startswith("_")
            and not inspect.isroutine(val)
            and name not in ("predecessors", "inputs")
        ):
            attrs[name] = val
    for cls in inspect.getmro(node.__class__):
        for name, val in cls.__dict__.items():
            if (
                not name.startswith("_")
                and not inspect.isroutine(val)
                and name not in attrs
                and name not in ("predecessors", "inputs")
            ):
                attrs[name] = getattr(node, name)
    return attrs


class DrawioIO:
    @staticmethod
    def compute_layout(graph: Graph, rankdir="LR"):
        dot = ["digraph G {", f"  graph [rankdir={rankdir}];"]
        for node in graph.nodes:
            dot.append(f'  "{node.id}";')
        for i, row in enumerate(graph.adjacencyMatrix):
            for j, c in enumerate(row):
                if c:
                    src, tgt = graph.nodes[i].id, graph.nodes[j].id
                    dot.append(f'  "{src}" -> "{tgt}";')
        dot.append("}")
        proc = subprocess.run(
            ["dot", "-Tplain"],
            input="\n".join(dot).encode(),
            stdout=subprocess.PIPE,
            check=True,
        )
        positions, max_y = {}, 0.0
        for line in proc.stdout.decode().splitlines():
            parts = line.split()
            if parts and parts[0] == "node":
                name, x, y = parts[1].strip('"'), float(parts[2]), float(parts[3])
                positions[name] = (x, y)
                max_y = max(max_y, y)
        # flip y
        for nid, (x, y) in list(positions.items()):
            positions[nid] = (x, max_y - y)
        return positions

    @staticmethod
    def save(
        graph: Graph,
        filename: str,
        cell_size=(80, 80),
        padding=20,
        canvas=None,
        preserve_visuals: bool = False,
    ):
        """Save a Graph to Draw.io XML format.

        If preserve_visuals is True and a canvas is provided (or nodes expose gui_pos/gui_color
        attributes), the node positions and colors will be embedded into the saved Draw.io file.
        Otherwise, a Graphviz (dot) layout is used to compute positions.
        """
        # If preserve_visuals requested, try to obtain positions from canvas or node attributes
        raw = None
        if preserve_visuals:
            # If we have a canvas with NodeItems, try to use those positions
            try:
                if canvas is not None and hasattr(canvas, "node_items"):
                    raw = {}
                    for node, item in canvas.node_items.items():
                        try:
                            pos = item.pos()
                            raw[node.id] = (pos.x(), pos.y())
                        except Exception:
                            # If NodeItem has x/y attributes instead
                            try:
                                raw[node.id] = (item.x, item.y)
                            except Exception:
                                pass
            except Exception:
                raw = None
            # If node objects carry gui_pos attributes (e.g. loaded from CGJson), use them
            if raw is None or len(raw) == 0:
                try:
                    raw = {}
                    for node in graph.nodes:
                        pos = getattr(node, "gui_pos", None)
                        if pos is not None:
                            raw[node.id] = (float(pos[0]), float(pos[1]))
                except Exception:
                    raw = None
        # Graphviz layout as fallback
        if raw is None or len(raw) == 0:
            raw = DrawioIO.compute_layout(graph)
        # Scale to draw.io
        positions = {
            nid: (x * cell_size[0], y * cell_size[1]) for nid, (x, y) in raw.items()
        }
        # Collision resolution
        moved = True
        while moved:
            moved = False
            for a, (ax, ay) in positions.items():
                for b, (bx, by) in positions.items():
                    if (
                        a != b
                        and abs(ax - bx) < cell_size[0]
                        and abs(ay - by) < cell_size[1]
                    ):
                        positions[b] = (bx + cell_size[0] + padding, by)
                        moved = True
        # Build draw.io XML
        mxfile = ET.Element("mxfile")
        diagram = ET.SubElement(mxfile, "diagram", {"name": "Graph", "id": "template"})
        model = ET.SubElement(diagram, "mxGraphModel", {"grid": "1", "gridSize": "10"})
        root_el = ET.SubElement(model, "root")
        ET.SubElement(root_el, "mxCell", {"id": "0"})
        ET.SubElement(root_el, "mxCell", {"id": "1", "parent": "0"})
        # Nodes
        for node in graph.nodes:
            attrs = get_node_attributes(node)
            attrs.update(
                {
                    "id": node.id,
                    "NodeType": type(node).__name__,
                    "NodeName": node.name,
                    "NodeValue": node.value,
                    "label": f"{node.name}\n{node.value}\n{type(node).__name__}",
                }
            )
            # If the graph or canvas carries visual information (gui_pos/gui_color), include it
            if preserve_visuals:
                # Prefer canvas node item color/position
                gui_x, gui_y, gui_w, gui_h = None, None, None, None
                gui_color = None
                label_color = None
                if (
                    canvas is not None
                    and hasattr(canvas, "node_items")
                    and node in canvas.node_items
                ):
                    item = canvas.node_items[node]
                    try:
                        pos = item.pos()
                        gui_x, gui_y = pos.x(), pos.y()
                    except Exception:
                        pass
                    try:
                        gui_color = (
                            item.manual_color.name()
                            if getattr(item, "manual_color", None) is not None
                            else (
                                item.color.name()
                                if getattr(item, "color", None) is not None
                                else None
                            )
                        )
                    except Exception:
                        gui_color = None
                    # label color
                    label_color = None
                    try:
                        if hasattr(item, "label") and item.label is not None:
                            lc = item.label.defaultTextColor()
                            if lc is not None:
                                label_color = lc.name()
                    except Exception:
                        label_color = None
                    try:
                        gui_w = item.rect().width()
                        gui_h = item.rect().height()
                    except Exception:
                        pass
                # If not available on canvas, fallback to node attributes
                if gui_x is None or gui_y is None:
                    pos = getattr(node, "gui_pos", None)
                    if pos is not None:
                        try:
                            gui_x = float(pos[0])
                            gui_y = float(pos[1])
                        except Exception:
                            pass
                    if gui_color is None:
                        try:
                            gui_color = getattr(node, "gui_color", None)
                        except Exception:
                            gui_color = None
                # store GUI visuals attributes on the object for DrawioIO.load to restore
                if gui_x is not None and gui_y is not None:
                    attrs["gui_pos"] = f"{gui_x},{gui_y}"
                if gui_color is not None:
                    attrs["gui_color"] = str(gui_color)
                if label_color is not None:
                    attrs["gui_label_color"] = str(label_color)
                if gui_w is not None and gui_h is not None:
                    try:
                        attrs["gui_radius"] = str(float(gui_w) / 2.0)
                    except Exception:
                        pass
                # Gui label can be stored separately if present
                gui_label = getattr(node, "gui_label", None)
                if gui_label is not None:
                    attrs["gui_label"] = str(gui_label)
            str_attrs = {k: str(v) for k, v in attrs.items()}
            obj = ET.SubElement(root_el, "object", str_attrs)
            # build style string: base + optional color/shape + font color
            style_str = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;"
            gui_col = attrs.get("gui_color") or getattr(node, "gui_color", None)
            if gui_col:
                style_str += f"fillColor={gui_col};"
            # label font color
            label_col = attrs.get("gui_label_color") or getattr(
                node, "gui_label_color", None
            )
            if label_col:
                style_str += f"fontColor={label_col};"
            ET.SubElement(
                obj,
                "mxCell",
                {
                    "style": style_str,
                    "vertex": "1",
                    "parent": "1",
                },
            )
            # geometry: prefer explicit gui_pos when present, else use computed positions
            g_x, g_y = None, None
            if preserve_visuals:
                pos_attr = None
                try:
                    pos_attr = obj.get("gui_pos")
                except Exception:
                    pos_attr = None
                if pos_attr:
                    try:
                        g_x, g_y = [float(v) for v in pos_attr.split(",")]
                    except Exception:
                        g_x, g_y = None, None
            if g_x is None or g_y is None:
                x, y = positions.get(node.id, (0, 0))
            else:
                x, y = g_x, g_y
            # Set geometry width/height based on cell_size or gui_radius if provided
            w = cell_size[0]
            h = cell_size[1]
            try:
                # prefer explicit gui_radius (node.gui_radius or attrs)
                rad = None
                if "gui_radius" in attrs:
                    try:
                        rad = float(attrs.get("gui_radius"))
                    except Exception:
                        rad = None
                else:
                    rad = getattr(node, "gui_radius", None)
                if rad is not None:
                    w = rad * 2
                    h = rad * 2
            except Exception:
                pass
            ET.SubElement(
                obj.find("mxCell"),
                "mxGeometry",
                {
                    "x": str(x),
                    "y": str(y),
                    "width": str(w),
                    "height": str(h),
                    "as": "geometry",
                },
            )
        # Edges
        for i, node in enumerate(graph.nodes):
            for pred in node.predecessors:
                edge = ET.SubElement(
                    root_el,
                    "mxCell",
                    {
                        "id": f"e{i}_{pred.id}_{node.id}",
                        "edge": "1",
                        "source": pred.id,
                        "target": node.id,
                        "parent": "1",
                        "style": "edgeStyle=elbowEdgeStyle;elbow=horizontal;curved=1;html=1;",
                    },
                )
                ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})
        ET.ElementTree(mxfile).write(filename, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def load(filename: str) -> Graph:
        tree = ET.parse(filename)
        root = tree.getroot().find(".//root")
        graph = Graph()
        id_map = {}
        for obj in root.findall("object"):
            nid = obj.get("id")
            ntype = obj.get("NodeType", "DisplayNode")
            cls = NODE_TYPE_MAP.get(ntype, DisplayNode)
            node = cls(name=obj.get("NodeName", nid))
            node.predecessors = []
            for k, v in obj.items():
                if k in ("id", "NodeType", "label"):
                    continue
                if k == "NodeName":
                    node.name = v
                elif k == "NodeValue":
                    node.value = float(v)
                else:
                    if v.lower() in ("true", "false"):
                        val = v.lower() == "true"
                    else:
                        try:
                            val = int(v)
                        except:
                            try:
                                val = float(v)
                            except:
                                val = v
                    # Special-case gui_pos - parse 'x,y' into a tuple
                    if k == "gui_pos":
                        try:
                            parts = str(val).split(",")
                            node.gui_pos = (float(parts[0]), float(parts[1]))
                        except Exception:
                            try:
                                # fallback to list or single value
                                node.gui_pos = tuple(val)
                            except Exception:
                                node.gui_pos = val
                    else:
                        setattr(node, k, val)
            # Parse mxCell geometry/style into gui_pos/gui_color/gui_radius if present
            try:
                mx_cell = obj.find("mxCell")
                if mx_cell is not None:
                    geom = mx_cell.find("mxGeometry")
                    if geom is not None:
                        x = geom.get("x")
                        y = geom.get("y")
                        width = geom.get("width")
                        height = geom.get("height")
                        if x is not None and y is not None:
                            try:
                                node.gui_pos = (float(x), float(y))
                            except Exception:
                                pass
                        if width is not None:
                            try:
                                node.gui_radius = float(width) / 2.0
                            except Exception:
                                pass
                    style = mx_cell.get("style")
                    if style:
                        # parse style string like key=value;key2=value2
                        try:
                            items = [s for s in style.split(";") if "=" in s]
                            for it in items:
                                key, val = it.split("=", 1)
                                if key == "fillColor":
                                    node.gui_color = val
                                if key == "strokeColor":
                                    node.gui_stroke = val
                                if key == "shape":
                                    node.gui_shape = val
                                if key == "fontColor":
                                    node.gui_label_color = val
                        except Exception:
                            pass
            except Exception:
                pass
            graph.AddNode(node)
            id_map[nid] = node
        for cell in root.findall('mxCell[@edge="1"]'):
            src, tgt = cell.get("source"), cell.get("target")
            if src in id_map and tgt in id_map:
                graph.ConnectPreNode(id_map[tgt], id_map[src])
        return graph

    @staticmethod
    def generate_template_graph(filename: str, cell_size=(80, 80)):
        graph = Graph()
        for node_type, cls in NODE_TYPE_MAP.items():
            node = cls(name=node_type)
            graph.AddNode(node)
        DrawioIO.save(graph, filename, cell_size)
