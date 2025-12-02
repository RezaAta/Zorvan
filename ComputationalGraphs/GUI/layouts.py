"""
Graph layout algorithms for computational graphs.

Provides hierarchical, tree, and MLP-specific layout algorithms suited for
computational graphs (DAGs with data flow), not data visualization.

Layout algorithms:
- sugiyama_layout: Sugiyama algorithm for general DAGs (hierarchical layers)
- tree_layout: Walker's algorithm for tree-structured graphs
- mlp_layered_layout: MLP-specific layout using node name patterns
"""

import re
from typing import Any, Dict, List, Optional, Tuple

# Try to import grandalf for Sugiyama layout
try:
    from grandalf.graphs import Edge
    from grandalf.graphs import Graph as GrandalfGraph
    from grandalf.graphs import Vertex
    from grandalf.layouts import SugiyamaLayout

    GRANDALF_AVAILABLE = True
except ImportError:
    GRANDALF_AVAILABLE = False

# NetworkX fallback
try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


def sugiyama_layout(
    nodes: List[Any],
    get_predecessors: callable,
    node_width: float = 80,
    node_height: float = 80,
    layer_spacing: float = 150,
    node_spacing: float = 100,
    direction: str = "LR",
) -> Dict[Any, Tuple[float, float]]:
    """
    Sugiyama hierarchical layout algorithm for DAGs.

    Uses the grandalf library if available, otherwise falls back to NetworkX.

    Args:
        nodes: List of node objects
        get_predecessors: Function that returns predecessors for a node
        node_width: Width of each node for spacing calculation
        node_height: Height of each node for spacing calculation
        layer_spacing: Horizontal spacing between layers (for LR) or vertical (for TB)
        node_spacing: Vertical spacing between nodes in same layer (for LR)
        direction: 'LR' (left-to-right) or 'TB' (top-to-bottom)

    Returns:
        Dictionary mapping nodes to (x, y) positions
    """
    if not nodes:
        return {}

    if GRANDALF_AVAILABLE:
        return _sugiyama_grandalf(
            nodes,
            get_predecessors,
            node_width,
            node_height,
            layer_spacing,
            node_spacing,
            direction,
        )
    elif NETWORKX_AVAILABLE:
        return _sugiyama_networkx_fallback(
            nodes, get_predecessors, layer_spacing, node_spacing, direction
        )
    else:
        # Ultimate fallback: simple grid
        return _simple_grid_layout(nodes, node_spacing)


def _sugiyama_grandalf(
    nodes: List[Any],
    get_predecessors: callable,
    node_width: float,
    node_height: float,
    layer_spacing: float,
    node_spacing: float,
    direction: str,
) -> Dict[Any, Tuple[float, float]]:
    """Sugiyama layout using grandalf library."""

    # Build grandalf graph
    # Create vertices with size hints
    node_to_vertex = {}
    for node in nodes:
        v = Vertex(node)
        # Set vertex view dimensions for layout
        v.view = _VertexView(node_width, node_height)
        node_to_vertex[node] = v

    # Create edges (from predecessors to node)
    edges = []
    for node in nodes:
        v_target = node_to_vertex[node]
        for pred in get_predecessors(node):
            if pred in node_to_vertex:
                v_source = node_to_vertex[pred]
                edges.append(Edge(v_source, v_target))

    # Build grandalf graph
    vertices = list(node_to_vertex.values())
    g = GrandalfGraph(vertices, edges)

    # Apply Sugiyama layout
    # grandalf expects connected components, handle disconnected graphs
    positions = {}
    x_offset = 0

    for component in g.C:
        sug = SugiyamaLayout(component)
        sug.init_all()
        sug.draw()  # Computes positions

        # Extract positions from vertices
        min_x = float("inf")
        min_y = float("inf")
        for v in component.sV:
            if v.view.xy is not None:
                min_x = min(min_x, v.view.xy[0])
                min_y = min(min_y, v.view.xy[1])

        # Normalize and offset positions
        for v in component.sV:
            if v.view.xy is not None:
                x, y = v.view.xy
                # Normalize to start from 0
                x = x - min_x + x_offset
                y = y - min_y

                if direction == "LR":
                    # grandalf does TB by default, swap for LR
                    positions[v.data] = (
                        y * layer_spacing / node_height,
                        x * node_spacing / node_width,
                    )
                else:  # TB
                    positions[v.data] = (
                        x * node_spacing / node_width,
                        y * layer_spacing / node_height,
                    )

        # Update offset for next component
        if component.sV:
            max_x = max((v.view.xy[0] if v.view.xy else 0) for v in component.sV)
            x_offset = max_x + layer_spacing * 2

    return positions


class _VertexView:
    """Simple view class for grandalf vertices."""

    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h
        self.xy = None  # Will be set by layout


def _sugiyama_networkx_fallback(
    nodes: List[Any],
    get_predecessors: callable,
    layer_spacing: float,
    node_spacing: float,
    direction: str,
) -> Dict[Any, Tuple[float, float]]:
    """Fallback Sugiyama-like layout using NetworkX topological layering."""

    # Build NetworkX graph
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node)
        for pred in get_predecessors(node):
            if pred in nodes:
                G.add_edge(pred, node)

    # Assign layers using longest path from sources
    layers = _assign_layers_longest_path(G)

    # Position nodes within layers
    positions = {}
    layer_nodes = {}
    for node, layer in layers.items():
        if layer not in layer_nodes:
            layer_nodes[layer] = []
        layer_nodes[layer].append(node)

    # Sort layers and position nodes
    for layer_idx in sorted(layer_nodes.keys()):
        nodes_in_layer = layer_nodes[layer_idx]
        # Center nodes vertically in layer
        start_y = -(len(nodes_in_layer) - 1) * node_spacing / 2

        for i, node in enumerate(nodes_in_layer):
            if direction == "LR":
                x = layer_idx * layer_spacing
                y = start_y + i * node_spacing
            else:  # TB
                x = start_y + i * node_spacing
                y = layer_idx * layer_spacing
            positions[node] = (x, y)

    return positions


def _assign_layers_longest_path(G: "nx.DiGraph") -> Dict[Any, int]:
    """Assign layers to nodes based on longest path from sources."""
    layers = {}

    # Find source nodes (no predecessors)
    sources = [n for n in G.nodes() if G.in_degree(n) == 0]

    if not sources:
        # Graph has cycles, use all nodes as potential sources
        sources = list(G.nodes())

    # BFS/DFS to assign layers
    visited = set()
    queue = [(s, 0) for s in sources]

    while queue:
        node, layer = queue.pop(0)

        # Take maximum layer if already visited (longest path)
        if node in layers:
            if layer > layers[node]:
                layers[node] = layer
            else:
                continue
        else:
            layers[node] = layer

        for succ in G.successors(node):
            queue.append((succ, layer + 1))

    # Handle any remaining unvisited nodes (in cycles)
    for node in G.nodes():
        if node not in layers:
            layers[node] = 0

    return layers


def tree_layout(
    nodes: List[Any],
    get_predecessors: callable,
    node_spacing: float = 100,
    level_spacing: float = 150,
    direction: str = "LR",
) -> Dict[Any, Tuple[float, float]]:
    """
    Tree layout using Walker's algorithm (tidier drawings of trees).

    Best for tree-structured graphs. Falls back to hierarchical for DAGs.

    Args:
        nodes: List of node objects
        get_predecessors: Function that returns predecessors for a node
        node_spacing: Minimum horizontal spacing between sibling nodes
        level_spacing: Vertical spacing between tree levels
        direction: 'LR' (left-to-right) or 'TB' (top-to-bottom)

    Returns:
        Dictionary mapping nodes to (x, y) positions
    """
    if not nodes:
        return {}

    # Build adjacency for successors
    successors = {node: [] for node in nodes}
    roots = []
    node_set = set(nodes)

    for node in nodes:
        preds = [p for p in get_predecessors(node) if p in node_set]
        if not preds:
            roots.append(node)
        for pred in preds:
            if pred in successors:
                successors[pred].append(node)

    if not roots:
        # No roots found, use first node
        roots = [nodes[0]]

    # Simple recursive tree layout
    positions = {}
    x_counter = [0]  # Use list for closure mutation

    def layout_subtree(node: Any, depth: int, visited: set) -> float:
        """Layout a subtree, returns the x position of the node."""
        if node in visited:
            return x_counter[0]
        visited.add(node)

        children = [c for c in successors.get(node, []) if c not in visited]

        if not children:
            # Leaf node
            x = x_counter[0]
            x_counter[0] += node_spacing
            if direction == "LR":
                positions[node] = (depth * level_spacing, x)
            else:
                positions[node] = (x, depth * level_spacing)
            return x

        # Layout children first
        child_positions = []
        for child in children:
            child_x = layout_subtree(child, depth + 1, visited)
            child_positions.append(child_x)

        # Center parent over children
        x = sum(child_positions) / len(child_positions)
        if direction == "LR":
            positions[node] = (depth * level_spacing, x)
        else:
            positions[node] = (x, depth * level_spacing)

        return x

    # Layout each root tree
    visited = set()
    for root in roots:
        layout_subtree(root, 0, visited)

    # Handle any unvisited nodes (disconnected or in cycles)
    for node in nodes:
        if node not in positions:
            x = x_counter[0]
            x_counter[0] += node_spacing
            positions[node] = (0, x) if direction == "LR" else (x, 0)

    return positions


def mlp_layered_layout(
    nodes: List[Any],
    get_predecessors: callable,
    node_spacing: float = 100,
    layer_spacing: float = 200,
    direction: str = "LR",
) -> Dict[Any, Tuple[float, float]]:
    """
    MLP-specific layered layout using node name patterns.

    Detects neural network structure from node names:
    - Input nodes: x0, x1, ... or names containing 'input'
    - Buffer nodes: Buff_x0, Buff_x1, ...
    - Weight nodes: W_x0H0N1, W_H0N1y0, ...
    - Multiplication nodes: mult, Mult, ...
    - Addition nodes: add, Add, sum, Sum, ...
    - Activation nodes: sigmoid, relu, tanh, ...
    - Output nodes: y0, y1, ... or names containing 'output'
    - Error/Loss nodes: loss, error, Loss, Error, MSE, ...
    - Gradient nodes: dW, grad, EG, ...

    Args:
        nodes: List of node objects
        get_predecessors: Function that returns predecessors for a node
        node_spacing: Vertical spacing between nodes in same layer
        layer_spacing: Horizontal spacing between layers
        direction: 'LR' (left-to-right) or 'TB' (top-to-bottom)

    Returns:
        Dictionary mapping nodes to (x, y) positions
    """
    if not nodes:
        return {}

    # Categorize nodes by patterns
    categories = {
        "input": [],  # Layer 0
        "buffer": [],  # Layer 1
        "weight": [],  # Layer 2
        "mult": [],  # Layer 3
        "add": [],  # Layer 4
        "activation": [],  # Layer 5
        "output": [],  # Layer 6
        "loss": [],  # Layer 7
        "gradient": [],  # Layer 8
        "other": [],  # Fallback
    }

    # Pattern matching for node classification
    patterns = {
        "input": [r"^x\d+$", r"input", r"Input", r"^DataStream"],
        "buffer": [r"^Buff_", r"Buffer"],
        "weight": [r"^W_", r"weight", r"Weight", r"^Container"],
        "mult": [r"mult", r"Mult", r"\*"],
        "add": [r"^add", r"^Add", r"^sum", r"^Sum", r"\+", r"^a\d+$"],
        "activation": [
            r"sigmoid",
            r"Sigmoid",
            r"relu",
            r"ReLU",
            r"tanh",
            r"Tanh",
            r"softmax",
            r"Softmax",
            r"^act",
            r"^Act",
        ],
        "output": [r"^y\d+$", r"output", r"Output", r"^out", r"^Out"],
        "loss": [r"loss", r"Loss", r"error", r"Error", r"MSE", r"mse", r"CrossEntropy"],
        "gradient": [
            r"^dW",
            r"^dw",
            r"^grad",
            r"^Grad",
            r"^EG",
            r"^LRMult",
            r"delta",
            r"Delta",
        ],
    }

    def categorize_node(node: Any) -> str:
        """Determine category of a node based on its name."""
        name = getattr(node, "name", str(node))

        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, name):
                    return category
        return "other"

    # Categorize all nodes
    for node in nodes:
        cat = categorize_node(node)
        categories[cat].append(node)

    # Define layer order
    layer_order = [
        "input",
        "buffer",
        "weight",
        "mult",
        "add",
        "activation",
        "output",
        "loss",
        "gradient",
        "other",
    ]

    # Assign positions
    positions = {}
    layer_idx = 0

    for category in layer_order:
        cat_nodes = categories[category]
        if not cat_nodes:
            continue

        # Sort nodes within category for consistent ordering
        cat_nodes.sort(key=lambda n: getattr(n, "name", str(n)))

        # Center nodes vertically
        start_y = -(len(cat_nodes) - 1) * node_spacing / 2

        for i, node in enumerate(cat_nodes):
            if direction == "LR":
                x = layer_idx * layer_spacing
                y = start_y + i * node_spacing
            else:  # TB
                x = start_y + i * node_spacing
                y = layer_idx * layer_spacing
            positions[node] = (x, y)

        layer_idx += 1

    return positions


def _simple_grid_layout(
    nodes: List[Any], spacing: float = 100
) -> Dict[Any, Tuple[float, float]]:
    """Simple grid layout as ultimate fallback."""
    import math

    n = len(nodes)
    cols = max(1, int(math.sqrt(n)))

    positions = {}
    for i, node in enumerate(nodes):
        row = i // cols
        col = i % cols
        positions[node] = (col * spacing, row * spacing)

    return positions


def get_available_layouts() -> List[str]:
    """Return list of available layout algorithms."""
    layouts = ["mlp_layout", "mlp_layered", "tree"]

    if GRANDALF_AVAILABLE or NETWORKX_AVAILABLE:
        layouts.insert(0, "sugiyama")  # Preferred if available

    return layouts


def is_grandalf_available() -> bool:
    """Check if grandalf library is available."""
    return GRANDALF_AVAILABLE


def is_networkx_available() -> bool:
    """Check if NetworkX library is available."""
    return NETWORKX_AVAILABLE


# =============================================================================
# MLP Layout Algorithm - Manual layout tailored for computational graphs
# =============================================================================


class MLPLayoutEngine:
    """
    Manual MLP layout algorithm tailored for computational graph neural networks.

    Uses node name matching and topological position to place nodes according to
    the MLP structure (forward pass + backpropagation).
    """

    def __init__(self, nodes: List[Any], grid_size: float = 80):
        """
        Initialize the MLP layout engine.

        Args:
            nodes: List of all nodes in the graph
            grid_size: Grid cell size in pixels (e.g., 120 = each cell is 120x120 pixels)

        Coordinate System:
            - X: positive = right, negative = left
            - Y: positive = DOWN (screen coordinates), but algorithm uses
                 mathematical coordinates where +Y = UP, so we negate Y internally
            - When algorithm says (+1, +1) offset = "right and up" = screen (+1, -1)
        """
        self.nodes = nodes
        self.grid_size = grid_size
        self.positions: Dict[Any, Tuple[float, float]] = {}
        self.placed: set = set()  # Track placed nodes

        # Build lookup structures
        self.node_by_name: Dict[str, Any] = {}
        self.successors: Dict[Any, List[Any]] = {n: [] for n in nodes}
        self.predecessors: Dict[Any, List[Any]] = {n: [] for n in nodes}

        for node in nodes:
            name = getattr(node, "name", str(node))
            self.node_by_name[name] = node

            # Build predecessor/successor maps
            preds = getattr(node, "predecessors", [])
            self.predecessors[node] = [p for p in preds if p in nodes]
            for pred in self.predecessors[node]:
                if pred in self.successors:
                    self.successors[pred].append(node)

    def grid_pos(self, gx: int, gy: int) -> Tuple[float, float]:
        """Convert grid coordinates to pixel coordinates.

        Note: gy is in mathematical coordinates (+Y = up),
        so we negate it for screen coordinates (+Y = down).

        Returns exact integer positions to ensure grid alignment.
        """
        # Use integer arithmetic to avoid floating point errors
        px = int(gx) * int(self.grid_size)
        py = -int(gy) * int(self.grid_size)
        return (float(px), float(py))

    def place_node(self, node: Any, gx: int, gy: int) -> bool:
        """
        Place a node at grid position if not already placed.

        Args:
            gx: Grid X coordinate (positive = right)
            gy: Grid Y coordinate (positive = UP in mathematical coords)

        Returns True if placed, False if already placed.
        """
        if node in self.placed:
            return False
        self.positions[node] = self.grid_pos(gx, gy)
        self.placed.add(node)
        return True

    def get_grid_coords(self, node: Any) -> Tuple[int, int]:
        """Get the grid coordinates of a placed node.

        Returns (gx, gy) in mathematical coordinates.
        """
        if node not in self.positions:
            return (0, 0)
        px, py = self.positions[node]
        # Convert back: py = -gy * grid_size, so gy = -py / grid_size
        return (int(px / self.grid_size), int(-py / self.grid_size))

    def get_node_name(self, node: Any) -> str:
        """Get the name of a node."""
        return getattr(node, "name", str(node))

    def get_last_number(self, node: Any) -> int:
        """Extract the last number from a node's name for sorting.

        E.g., 'Mul_x0H0N1' -> 1, 'Add_L0N2' -> 2, 'W_x0H0N0' -> 0
        """
        name = self.get_node_name(node)
        # Find all numbers in the name
        numbers = re.findall(r"\d+", name)
        if numbers:
            return int(numbers[-1])
        return 0

    def get_neuron_number(self, node: Any) -> int:
        """Extract the neuron number (after 'N') from a node's name for sorting.

        E.g., 'W_H0N1y0' -> 1, 'W_H0N0y0' -> 0, 'Mul_x0H0N2' -> 2
        For weights like W_x0H0N1, this returns 1 (the N index).
        """
        name = self.get_node_name(node)
        # Look for N followed by a number
        match = re.search(r"N(\d+)", name)
        if match:
            return int(match.group(1))
        # Fallback to last number
        return self.get_last_number(node)

    def get_node_type(self, node: Any) -> str:
        """Get the type name of a node."""
        return type(node).__name__

    def find_nodes_by_pattern(self, pattern: str) -> List[Any]:
        """Find all nodes matching a regex pattern."""
        regex = re.compile(pattern)
        return [n for n in self.nodes if regex.match(self.get_node_name(n))]

    def find_nodes_by_type(self, type_name: str) -> List[Any]:
        """Find all nodes of a specific type."""
        return [n for n in self.nodes if type_name in self.get_node_type(n)]

    def get_successors_by_pattern(self, node: Any, pattern: str) -> List[Any]:
        """Get successor nodes matching a pattern."""
        regex = re.compile(pattern)
        return [
            s
            for s in self.successors.get(node, [])
            if regex.match(self.get_node_name(s))
        ]

    def get_predecessors_by_pattern(self, node: Any, pattern: str) -> List[Any]:
        """Get predecessor nodes matching a pattern."""
        regex = re.compile(pattern)
        return [
            p
            for p in self.predecessors.get(node, [])
            if regex.match(self.get_node_name(p))
        ]

    def get_successors_by_type(self, node: Any, type_name: str) -> List[Any]:
        """Get successor nodes of a specific type."""
        return [
            s
            for s in self.successors.get(node, [])
            if type_name in self.get_node_type(s)
        ]

    def get_predecessors_by_type(self, node: Any, type_name: str) -> List[Any]:
        """Get predecessor nodes of a specific type."""
        return [
            p
            for p in self.predecessors.get(node, [])
            if type_name in self.get_node_type(p)
        ]

    def layout(self) -> Dict[Any, Tuple[float, float]]:
        """
        Execute the full MLP layout algorithm.

        Returns positions dict mapping nodes to (x, y) pixel coordinates.
        """
        self._layout_forward_pass()
        self._layout_derivative_nodes()  # Place D_ nodes based on their predecessors
        self._layout_backprop()
        self._layout_remaining_nodes()
        return self.positions

    def _layout_derivative_nodes(self):
        """Place derivative nodes at (+1, +1) from their predecessor.

        Derivative nodes (D_H0N0, D_y0, etc.) take an activation or buffer as input.
        They should be placed at (+1, +1) offset from their predecessor node.
        This works for both buffered (concurrent) and forward processing graphs.
        """
        # Find all derivative nodes
        deriv_nodes = self.find_nodes_by_pattern(r"^D_H\d+N\d+$|^D_L\d+N\d+$|^D_y\d+$")

        for deriv in deriv_nodes:
            if deriv in self.placed:
                continue

            # Get the predecessor nodes (the node this derivative takes as input)
            preds = self.predecessors.get(deriv, [])

            # Find a placed predecessor to position relative to
            placed_pred = None
            for pred in preds:
                if pred in self.placed:
                    placed_pred = pred
                    break

            if placed_pred:
                # Place derivative at (+1, +1) from predecessor
                pred_gx, pred_gy = self.get_grid_coords(placed_pred)
                self.place_node(deriv, pred_gx + 1, pred_gy + 1)

    def _layout_forward_pass(self):
        """Layout the forward pass nodes."""
        # Step 1: Find and place input nodes (x0, x1, x2, ...)
        # x0 at top (highest screen Y), x1 below, etc.
        # In grid coords: higher Y = up on screen (due to negation in grid_pos)
        # So x0 gets highest Y, x1 gets lower Y, etc.
        input_nodes = self.find_nodes_by_pattern(r"^x\d+$")
        input_nodes.sort(key=lambda n: int(self.get_node_name(n)[1:]))

        num_inputs = len(input_nodes)
        base_x, base_y = 0, 0
        for i, input_node in enumerate(input_nodes):
            # x0 at top: Y = (num_inputs - 1) * 2, x1 below: Y = (num_inputs - 2) * 2, etc.
            # So x0 has highest Y (top), xN has lowest Y (bottom)
            self.place_node(input_node, base_x, base_y + (num_inputs - 1 - i) * 2)

        # Step 2: Place buffer nodes for each input at (+1, +1) offset
        for i, input_node in enumerate(input_nodes):
            buffers = self.get_successors_by_pattern(input_node, r"^Buff_x\d+$")
            for buf in buffers:
                input_gx, input_gy = self.get_grid_coords(input_node)
                # (+1, +1) = top-right of input
                self.place_node(buf, input_gx + 1, input_gy + 1)

        # Step 3: Place mult nodes for first hidden layer
        # Position: (+count+2, 0) for first mult, then column down
        # count = number of mult nodes
        first_layer_mults = self.find_nodes_by_pattern(r"^Mul_x\d+H\d+$")
        first_layer_mults.sort(key=lambda n: self.get_last_number(n))

        if first_layer_mults:
            count = len(first_layer_mults)
            mult_base_x = base_x + count + 2  # (+count+2, 0) from input origin
            # Place mults with Mul_x0H0N0 at top (highest Y), going down
            for j, mult in enumerate(first_layer_mults):
                # mult 0 at highest Y, mult N at lowest Y
                self.place_node(mult, mult_base_x, base_y + (count - 1 - j))

            # Step 4: Place weight nodes for mult nodes
            self._place_weights_for_mults(first_layer_mults, mult_base_x)

        # Step 5 & 6: Place Addition and Activation nodes for hidden layers
        self._layout_hidden_layers(base_x, base_y)

        # Step 7-9: Place output layer nodes
        self._layout_output_layer()

    def _place_weights_for_mults(self, mult_nodes: List[Any], mult_base_x: int):
        """Place weight nodes in a diagonal pattern above their multiplication nodes.

        Step 4: Collect all weight nodes from mult nodes, sort by neuron index,
        and place in a diagonal pattern going from bottom-left to top-right.
        Each weight gets a unique position based on its index t:
        - Weight 0: (-count, +1) from mult origin
        - Weight 1: (-count+1, +2) from mult origin
        - Weight t: (-count+t, +t+1) from mult origin

        This creates a diagonal line of weights.
        """
        # First, collect ALL weight nodes from all mult nodes to get total count
        all_weights = []
        mult_for_weight = {}  # Track which mult each weight belongs to

        for mult in mult_nodes:
            if mult not in self.positions:
                continue
            weights = self.get_predecessors_by_pattern(mult, r"^W_")
            if not weights:
                weights = self.get_predecessors_by_type(mult, "Container")
            for w in weights:
                if w not in mult_for_weight:  # Avoid duplicates
                    all_weights.append(w)
                    mult_for_weight[w] = mult

        # Sort weights by neuron number (N index) for consistent ordering
        all_weights.sort(key=lambda n: self.get_neuron_number(n))

        count = len(all_weights)
        if count == 0:
            return

        # Find the top-right mult position as reference point for diagonal
        max_mult_gx = mult_base_x
        max_mult_gy = 0
        for mult in mult_nodes:
            if mult in self.positions:
                gx, gy = self.get_grid_coords(mult)
                if gy > max_mult_gy:
                    max_mult_gy = gy

        # Place weights in diagonal: each weight at unique (x, y)
        # Starting from top-left, going down-right diagonally
        for t, weight in enumerate(all_weights):
            # Diagonal pattern: x increases, y decreases with t
            # Weight 0 at top-left: (base_x - count, max_y + count)
            # Weight t at: (base_x - count + t, max_y + count - t)
            wx = max_mult_gx - count + t
            wy = max_mult_gy + count - t
            self.place_node(weight, wx, wy)

    def _layout_hidden_layers(self, base_x: int, base_y: int):
        """Layout hidden layer nodes (Add, Activation, Buffer, Derivative)."""
        add_nodes = self.find_nodes_by_pattern(r"^Add_(L\d+N\d+|H\d+N\d+)$")
        add_nodes.sort(key=lambda n: self.get_last_number(n))

        layers: Dict[str, List[Any]] = {}
        for add in add_nodes:
            name = self.get_node_name(add)
            match = re.match(r"^Add_(L\d+|H\d+)", name)
            if match:
                layer_id = match.group(1)
                if layer_id not in layers:
                    layers[layer_id] = []
                layers[layer_id].append(add)

        # Find the rightmost mult node to position adds after it
        max_mult_x = base_x + 4
        mult_nodes = self.find_nodes_by_pattern(r"^Mul_")
        for mult in mult_nodes:
            if mult in self.positions:
                mult_gx, _ = self.get_grid_coords(mult)
                max_mult_x = max(max_mult_x, mult_gx)

        add_base_x = int(max_mult_x) + 2
        layer_offset = 0

        # Get total mult count to determine Y range for alignment
        first_layer_mults = self.find_nodes_by_pattern(r"^Mul_x\\d+H\\d+$")
        first_layer_mult_count = len(first_layer_mults) if first_layer_mults else 4

        for layer_id in sorted(layers.keys()):
            layer_adds = layers[layer_id]
            layer_adds.sort(key=lambda n: self.get_last_number(n))
            num_adds = len(layer_adds)

            for j, add_node in enumerate(layer_adds):
                add_gx = add_base_x + layer_offset
                # Add node 0 at top (highest Y), going down
                # Scale Y to span similar range as mult nodes
                add_gy = base_y + (num_adds - 1 - j)
                self.place_node(add_node, add_gx, add_gy)

                activations = self.get_successors_by_pattern(
                    add_node, r"^Act_|^Sigmoid|^ReLU|^Tanh"
                )
                if not activations:
                    activations = self.get_successors_by_pattern(add_node, r"^Buff_H")

                for act in activations:
                    act_gx = add_gx + 2
                    self.place_node(act, act_gx, add_gy)

                    # Buffer nodes after activation at (+1, +1) from activation
                    act_buffers = self.get_successors_by_pattern(
                        act, r"^Buff_H|^Buff_Act"
                    )
                    for buf in act_buffers:
                        buf_gx = act_gx + 1
                        buf_gy = add_gy + 1
                        self.place_node(buf, buf_gx, buf_gy)

                    # Find ALL next layer mult nodes to get count for positioning
                    # These are mults that take input from ANY activation in this layer
                    # Pattern excludes output layer mults (which have 'y' in the name)
                    next_mults = self.get_successors_by_pattern(
                        act, r"^Mul_H\d+N\d+H\d+N\d+$"
                    )
                    if not next_mults:
                        # Also try simpler pattern for hidden-to-hidden mults (exclude those with 'y')
                        all_successors = self.get_successors_by_pattern(act, r"^Mul_H")
                        next_mults = [
                            m
                            for m in all_successors
                            if "y" not in self.get_node_name(m)
                        ]
                    if next_mults:
                        # Collect ALL mults for this next layer to get total count
                        # Pattern: Mul_H{layer}N{neuron}... where layer matches
                        all_next_layer_mults = []
                        for nm in next_mults:
                            nm_name = self.get_node_name(nm)
                            # Extract layer info to find all mults in same layer
                            match = re.match(r"^Mul_(H\d+N\d+)", nm_name)
                            if match:
                                layer_pattern = match.group(1)[:2]  # e.g., "H0" or "H1"
                                # Find all mults for this target layer
                                all_layer_mults = self.find_nodes_by_pattern(
                                    rf"^Mul_{layer_pattern}N\d+"
                                )
                                for m in all_layer_mults:
                                    if m not in all_next_layer_mults:
                                        all_next_layer_mults.append(m)

                        all_next_layer_mults.sort(key=lambda n: self.get_last_number(n))
                        total_count = len(all_next_layer_mults)

                        # Position mult nodes at (+count+3, 0) from activation
                        mult_base_x = act_gx + total_count + 3

                        next_mults.sort(key=lambda n: self.get_last_number(n))
                        for nm in next_mults:
                            # Find index in the full sorted list
                            nm_idx = (
                                all_next_layer_mults.index(nm)
                                if nm in all_next_layer_mults
                                else 0
                            )
                            # Index 0 at top (highest Y)
                            nm_gy = base_y + (total_count - 1 - nm_idx)
                            self.place_node(nm, mult_base_x, nm_gy)

                        # Place weights for ALL mults in this layer at once
                        self._place_weights_for_mults(all_next_layer_mults, mult_base_x)

            layer_offset += 6

    def _layout_output_layer(self):
        """Layout output layer: mults, weights, adds, outputs, errors, derivatives, labels, MSE.

        This follows the same pattern as hidden layers:
        1. Find output layer mult nodes (Mul_H*y* pattern)
        2. Place them at (+count+3, 0) from the last activation
        3. Place their weights in diagonal pattern
        4. Place Add_y nodes
        5. Place y (activation/output) nodes
        6. Place derivative, error, label, MSE nodes
        """
        # Step 1: Find output layer mult nodes
        output_mults = self.find_nodes_by_pattern(r"^Mul_H\d+N\d+y\d+$")
        output_mults.sort(key=lambda n: self.get_neuron_number(n))

        if output_mults:
            # Find the rightmost placed node to position output mults
            max_x = 0
            for node in self.placed:
                gx, _ = self.get_grid_coords(node)
                max_x = max(max_x, gx)

            total_count = len(output_mults)
            # Position mult nodes at (+count+3, 0) from max_x, like hidden layers
            mult_base_x = int(max_x) + total_count + 3

            # Place mults with index 0 at top
            for j, mult in enumerate(output_mults):
                mult_gy = total_count - 1 - j
                self.place_node(mult, mult_base_x, mult_gy)

            # Place weights for output mults
            self._place_weights_for_mults(output_mults, mult_base_x)

        # Step 2: Find and place Add_y nodes
        add_y_nodes = self.find_nodes_by_pattern(r"^Add_y\d+$")
        add_y_nodes.sort(key=lambda n: self.get_last_number(n))

        if add_y_nodes:
            # Find rightmost mult or placed node
            max_x = 0
            for node in self.placed:
                gx, _ = self.get_grid_coords(node)
                max_x = max(max_x, gx)

            add_base_x = int(max_x) + 2
            num_adds = len(add_y_nodes)

            for j, add_node in enumerate(add_y_nodes):
                # Add node 0 at top
                add_gy = num_adds - 1 - j
                self.place_node(add_node, add_base_x, add_gy)

        # Step 3: Find and place output activation/y nodes
        output_nodes = self.find_nodes_by_pattern(r"^y\d+$")
        if not output_nodes:
            output_nodes = self.find_nodes_by_pattern(r"^Act_y\d+$")
        output_nodes.sort(key=lambda n: self.get_last_number(n))

        if output_nodes:
            # Position relative to Add_y if exists, otherwise from max_x
            if add_y_nodes:
                # Get position of first Add_y
                add_gx, _ = self.get_grid_coords(add_y_nodes[0])
                out_base_x = add_gx + 2
            else:
                max_x = 0
                for node in self.placed:
                    gx, _ = self.get_grid_coords(node)
                    max_x = max(max_x, gx)
                out_base_x = int(max_x) + 2

            num_outputs = len(output_nodes)

            for i, output in enumerate(output_nodes):
                # Output 0 at top (highest Y), going down
                out_gy = num_outputs - 1 - i
                self.place_node(output, out_base_x, out_gy)

                # Derivative at (+1, +1) = top-right of output
                derivatives = self.get_successors_by_pattern(output, r"^D_y|Derivative")
                for deriv in derivatives:
                    self.place_node(deriv, out_base_x + 1, out_gy + 1)

                # Error at (+2, 0) = right of output
                errors = self.get_successors_by_pattern(
                    output, r"^Error_y|^error|Error"
                )
                for error in errors:
                    self.place_node(error, out_base_x + 2, out_gy)

                    # Label at (+1, -1) from error = bottom-right of error
                    labels = self.get_predecessors_by_pattern(
                        error, r"^L_y|^label|Label"
                    )
                    for label in labels:
                        self.place_node(label, out_base_x + 3, out_gy - 1)

                    # MSE at (+2, 0) from error
                    mse_nodes = self.get_successors_by_pattern(
                        error, r"^MSE|^mse|Loss|loss"
                    )
                    for mse in mse_nodes:
                        self.place_node(mse, out_base_x + 4, out_gy)

    def _layout_backprop(self):
        """Layout backpropagation nodes."""
        # Step 1: Place dW nodes above weight nodes at (0, +4)
        weight_nodes = self.find_nodes_by_pattern(r"^W_")
        for weight in weight_nodes:
            if weight not in self.positions:
                continue
            w_gx, w_gy = self.get_grid_coords(weight)

            dw_nodes = self.get_predecessors_by_pattern(weight, r"^dW_|^dw_")
            for dw in dw_nodes:
                # (0, +4) = directly above the weight
                self.place_node(dw, w_gx, w_gy + 4)

        # Step 2: Place LRMult nodes at (+1, +1) from dW nodes
        dw_nodes = self.find_nodes_by_pattern(r"^dW_|^dw_")
        for dw in dw_nodes:
            if dw not in self.positions:
                continue
            dw_gx, dw_gy = self.get_grid_coords(dw)

            lr_mults = self.get_predecessors_by_pattern(dw, r"^LRMult")
            for lr_mult in lr_mults:
                # (+1, +1) = top-right of dW
                self.place_node(lr_mult, dw_gx + 1, dw_gy + 1)

        # Step 3: Place EG nodes at (+3, +3) from error nodes
        error_nodes = self.find_nodes_by_pattern(r"^Error_y|^error")
        for error in error_nodes:
            if error not in self.positions:
                continue
            e_gx, e_gy = self.get_grid_coords(error)

            eg_nodes = self.get_successors_by_pattern(error, r"^EG_y")
            for eg in eg_nodes:
                # (+3, +3) = top-right diagonal from error
                self.place_node(eg, e_gx + 3, e_gy + 3)

        # Step 4: Place subsequent nodes of EG_y at (+count+t, +count)
        eg_y_nodes = self.find_nodes_by_pattern(r"^EG_y")
        for eg in eg_y_nodes:
            if eg not in self.positions:
                continue
            eg_gx, eg_gy = self.get_grid_coords(eg)

            successors = self.successors.get(eg, [])
            count = len(successors)
            for t, succ in enumerate(successors):
                # (+count+t, +count) from EG
                self.place_node(succ, eg_gx + count + t, eg_gy + count)

        # Step 5: Place WGS nodes at (-count, +count) from WG nodes (above WG)
        wg_nodes = self.find_nodes_by_pattern(r"^WG_")
        eg_count = len(eg_y_nodes)
        for wg in wg_nodes:
            if wg not in self.positions:
                continue
            wg_gx, wg_gy = self.get_grid_coords(wg)

            wgs_nodes = self.get_successors_by_pattern(wg, r"^WGS_")
            for wgs in wgs_nodes:
                # (-count, +count) = top-left diagonal from WG (WGS above WG)
                self.place_node(wgs, wg_gx - eg_count, wg_gy + eg_count)

        # Step 6: Place weight buffer nodes at (+1, +1) from weight
        for weight in weight_nodes:
            if weight not in self.positions:
                continue
            w_gx, w_gy = self.get_grid_coords(weight)

            buffers = self.get_successors_by_pattern(weight, r"^Buff_|^WNBuff_")
            for buf in buffers:
                # (+1, +1) = top-right of weight
                self.place_node(buf, w_gx + 1, w_gy + 1)

        # Step 7: Place hidden EG nodes at (-1, +1) from WGS nodes (above WGS)
        wgs_nodes = self.find_nodes_by_pattern(r"^WGS_")
        for wgs in wgs_nodes:
            if wgs not in self.positions:
                continue
            wgs_gx, wgs_gy = self.get_grid_coords(wgs)

            hidden_egs = self.get_successors_by_pattern(wgs, r"^EG_H")
            for heg in hidden_egs:
                # (-1, +1) = top-left of WGS (EG_H above WGS)
                self.place_node(heg, wgs_gx - 1, wgs_gy + 1)

        # Step 8: Place Learning Rate node above and centered
        lr_nodes = self.find_nodes_by_pattern(r"^LearningRate$|^lr$|^LR$")
        if not lr_nodes:
            for node in self.nodes:
                name = self.get_node_name(node)
                if not self.predecessors.get(node) and "Learning" in name:
                    lr_nodes.append(node)

        if lr_nodes and self.positions:
            # Find bounds in grid coordinates
            min_gx = min(self.get_grid_coords(n)[0] for n in self.placed)
            max_gx = max(self.get_grid_coords(n)[0] for n in self.placed)
            max_gy = max(
                self.get_grid_coords(n)[1] for n in self.placed
            )  # Highest Y = topmost

            center_gx = (min_gx + max_gx) // 2
            top_gy = max_gy + 3  # Above the topmost node

            for lr in lr_nodes:
                self.place_node(lr, center_gx, top_gy)

    def _layout_remaining_nodes(self):
        """Place any remaining unplaced nodes in a grid below the main layout."""
        unplaced = [n for n in self.nodes if n not in self.placed]
        if not unplaced:
            return

        # Find the lowest Y (most negative in grid coords = bottom of screen)
        min_gy = 0
        for node in self.placed:
            _, gy = self.get_grid_coords(node)
            min_gy = min(min_gy, gy)

        import math

        cols = max(1, int(math.sqrt(len(unplaced))))
        start_y = min_gy - 4  # Below the main layout

        for i, node in enumerate(unplaced):
            row = i // cols
            col = i % cols
            # Place in grid going down (decreasing Y)
            self.place_node(node, col * 2, start_y - row * 2)


def mlp_layout(
    nodes: List[Any],
    get_predecessors: callable = None,
    node_spacing: float = 80,
    layer_spacing: float = 80,
    direction: str = "LR",
) -> Dict[Any, Tuple[float, float]]:
    """
    MLP Layout algorithm - manual layout tailored for computational graph MLPs.

    Uses node name matching and topological position to place nodes according
    to the MLP forward pass and backpropagation structure.

    Args:
        nodes: List of node objects
        get_predecessors: Function that returns predecessors (optional, uses node.predecessors)
        node_spacing: Grid cell size for placement (default 80px)
        layer_spacing: Not used directly, included for API compatibility
        direction: 'LR' or 'TB' (currently only LR is implemented)

    Returns:
        Dictionary mapping nodes to (x, y) positions
    """
    if not nodes:
        return {}

    engine = MLPLayoutEngine(nodes, grid_size=node_spacing)
    return engine.layout()
