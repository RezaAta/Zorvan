import xml.etree.ElementTree as ET
import subprocess
import inspect
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.AbstractNode import AbstractNode
from ComputationalGraphs.Nodes.CompressedNode import CompressedNode
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.LinearNodeDerivative import LinearNodeDerivative
from ComputationalGraphs.Nodes.MeanSquaredErrorNode import MeanSquaredErrorNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
from ComputationalGraphs.Nodes.ReLUNode import ReLUNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
from ComputationalGraphs.Nodes.SigmoidDerivativeNode import SigmoidDerivativeNode
from ComputationalGraphs.Nodes.SubtractionNode import SubtractionNode

# Map draw.io node_type attribute to Python classes
NODE_TYPE_MAP = {
    'AdditionNode': AdditionNode,
    'DataStreamNode': DataStreamNode,
    'DisplayNode': DisplayNode,
    'AbstractNode': AbstractNode,
    'CompressedNode': CompressedNode,
    'ContainerNode': ContainerNode,
    'LinearNode': LinearNode,
    'LinearNodeDerivative': LinearNodeDerivative,
    'MeanSquaredErrorNode': MeanSquaredErrorNode,
    'MultiplicationNode': MultiplicationNode,
    'ReLUNode': ReLUNode,
    'SigmoidNode': SigmoidNode,
    'SigmoidDerivativeNode': SigmoidDerivativeNode,
    'SubtractionNode': SubtractionNode,
}


def get_node_attributes(node):
    """
    Introspect a node and return its non-callable, non-private attributes,
    excluding 'predecessors' and 'inputs'.
    """
    attrs = {}
    for name, val in vars(node).items():
        if not name.startswith('_') and not inspect.isroutine(val) and name not in ('predecessors', 'inputs'):
            attrs[name] = val
    for cls in inspect.getmro(node.__class__):
        for name, val in cls.__dict__.items():
            if not name.startswith('_') and not inspect.isroutine(val) and name not in attrs and name not in ('predecessors', 'inputs'):
                attrs[name] = getattr(node, name)
    return attrs

class DrawioIO:
    @staticmethod
    def compute_layout(graph: Graph, rankdir='LR'):
        dot = ['digraph G {', f'  graph [rankdir={rankdir}];']
        for node in graph.nodes:
            dot.append(f'  "{node.id}";')
        for i, row in enumerate(graph.adjacencyMatrix):
            for j, c in enumerate(row):
                if c:
                    src, tgt = graph.nodes[i].id, graph.nodes[j].id
                    dot.append(f'  "{src}" -> "{tgt}";')
        dot.append('}')
        proc = subprocess.run(['dot', '-Tplain'], input='\n'.join(dot).encode(), stdout=subprocess.PIPE, check=True)
        positions, max_y = {}, 0.0
        for line in proc.stdout.decode().splitlines():
            parts = line.split()
            if parts and parts[0] == 'node':
                name, x, y = parts[1].strip('"'), float(parts[2]), float(parts[3])
                positions[name] = (x, y)
                max_y = max(max_y, y)
        # flip y
        for nid, (x, y) in list(positions.items()):
            positions[nid] = (x, max_y - y)
        return positions

    @staticmethod
    def save(graph: Graph, filename: str, cell_size=(80, 80), padding=20):
        # Graphviz layout
        raw = DrawioIO.compute_layout(graph)
        # Scale to draw.io
        positions = {nid: (x * cell_size[0], y * cell_size[1]) for nid, (x, y) in raw.items()}
        # Collision resolution
        moved = True
        while moved:
            moved = False
            for a, (ax, ay) in positions.items():
                for b, (bx, by) in positions.items():
                    if a != b and abs(ax - bx) < cell_size[0] and abs(ay - by) < cell_size[1]:
                        positions[b] = (bx + cell_size[0] + padding, by)
                        moved = True
        # Build draw.io XML
        mxfile = ET.Element('mxfile')
        diagram = ET.SubElement(mxfile, 'diagram', {'name': 'Graph', 'id': 'template'})
        model = ET.SubElement(diagram, 'mxGraphModel', {'grid': '1', 'gridSize': '10'})
        root_el = ET.SubElement(model, 'root')
        ET.SubElement(root_el, 'mxCell', {'id': '0'})
        ET.SubElement(root_el, 'mxCell', {'id': '1', 'parent': '0'})
        # Nodes
        for node in graph.nodes:
            attrs = get_node_attributes(node)
            attrs.update({
                'id': node.id,
                'NodeType': type(node).__name__,
                'NodeName': node.name,
                'NodeValue': node.value,
                'label': f"{node.name}\n{node.value}\n{type(node).__name__}"
            })
            str_attrs = {k: str(v) for k, v in attrs.items()}
            obj = ET.SubElement(root_el, 'object', str_attrs)
            ET.SubElement(obj, 'mxCell', {
                'style': 'ellipse;whiteSpace=wrap;html=1;aspect=fixed;',
                'vertex': '1', 'parent': '1'
            })
            x, y = positions.get(node.id, (0, 0))
            ET.SubElement(obj.find('mxCell'), 'mxGeometry', {
                'x': str(x), 'y': str(y),
                'width': str(cell_size[0]), 'height': str(cell_size[1]),
                'as': 'geometry'
            })
        # Edges
        for i, node in enumerate(graph.nodes):
            for pred in node.predecessors:
                edge = ET.SubElement(root_el, 'mxCell', {
                    'id': f"e{i}_{pred.id}_{node.id}", 'edge': '1',
                    'source': pred.id, 'target': node.id, 'parent': '1',
                    'style': 'edgeStyle=elbowEdgeStyle;elbow=horizontal;curved=1;html=1;'
                })
                ET.SubElement(edge, 'mxGeometry', {'relative': '1', 'as': 'geometry'})
        ET.ElementTree(mxfile).write(filename, encoding='utf-8', xml_declaration=True)

    @staticmethod
    def load(filename: str) -> Graph:
        tree = ET.parse(filename)
        root = tree.getroot().find('.//root')
        graph = Graph()
        id_map = {}
        for obj in root.findall('object'):
            nid = obj.get('id')
            ntype = obj.get('NodeType', 'DisplayNode')
            cls = NODE_TYPE_MAP.get(ntype, DisplayNode)
            node = cls(name=obj.get('NodeName', nid))
            node.predecessors = []
            for k, v in obj.items():
                if k in ('id', 'NodeType', 'label'): continue
                if k == 'NodeName': node.name = v
                elif k == 'NodeValue': node.value = float(v)
                else:
                    if v.lower() in ('true', 'false'):
                        val = v.lower() == 'true'
                    else:
                        try: val = int(v)
                        except:
                            try: val = float(v)
                            except: val = v
                    setattr(node, k, val)
            graph.AddNode(node)
            id_map[nid] = node
        for cell in root.findall('mxCell[@edge="1"]'):
            src, tgt = cell.get('source'), cell.get('target')
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
