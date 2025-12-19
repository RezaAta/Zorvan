"""
Lightweight layout utilities for the new GUI framework.

This module wraps or falls back to the legacy layout algorithms found in
`ComputationalGraphs.GUI.layouts` when available, and provides simple
fallbacks otherwise. The goal is to offer a small, testable API for the
Canvas ViewModel to request node positions using a named layout.
"""

from typing import Any, Callable, Dict, List, Tuple

try:
    # Prefer reusing legacy implementation when available
    from ComputationalGraphs.GUI import layouts as legacy_layouts  # type: ignore

    LEGACY_AVAILABLE = True
except Exception:
    legacy_layouts = None
    LEGACY_AVAILABLE = False

# Optional dependency networkx for force/spring layout
try:
    import networkx as nx  # type: ignore

    NETWORKX_AVAILABLE = True
except Exception:
    nx = None
    NETWORKX_AVAILABLE = False


def apply_layout(
    nodes: List[Any],
    get_predecessors: Callable[[Any], List[Any]],
    algorithm: str = "sugiyama",
    direction: str = "LR",
    **kwargs
) -> Dict[str, Tuple[float, float]]:
    """Compute node positions for a list of nodes and return mapping from node.name to (x, y).

    Args:
        nodes: list of node objects (must have 'name' attribute)
        get_predecessors: callable(node) -> list of predecessor nodes
        algorithm: one of 'sugiyama', 'tree', 'circular', 'grid', 'force'
        direction: 'LR' (left-to-right) or 'TB' (top-to-bottom)
        kwargs: passed to underlying layout implementation

    Returns:
        Mapping node.name -> (x, y)
    """
    if not nodes:
        return {}

    # Use legacy functions if available for richer layouts
    if LEGACY_AVAILABLE:
        if algorithm == "sugiyama":
            pos = legacy_layouts.sugiyama_layout(
                nodes, get_predecessors, direction=direction, **kwargs
            )
        elif algorithm == "tree":
            pos = legacy_layouts.tree_layout(
                nodes, get_predecessors, direction=direction, **kwargs
            )
        elif algorithm == "ann" or algorithm == "mlp":
            pos = legacy_layouts.mlp_layered_layout(
                nodes, get_predecessors, direction=direction, **kwargs
            )
        else:
            # Fall back to simple grid/circular if requested algorithm is unknown
            pos = _simple_fallback(nodes, algorithm=algorithm, **kwargs)
    else:
        # No legacy module: use networkx spring if available, else simple fallback
        if algorithm in ("spring", "force") and NETWORKX_AVAILABLE:
            G = nx.Graph()
            for node in nodes:
                G.add_node(node)
                for p in get_predecessors(node):
                    if p in nodes:
                        G.add_edge(p, node)
            raw_pos = nx.spring_layout(G, **kwargs)
            pos = {node: raw_pos.get(node, (0.0, 0.0)) for node in nodes}
        else:
            pos = _simple_fallback(nodes, algorithm=algorithm, **kwargs)

    # Normalize and convert to mapping keyed by node.name
    result: Dict[str, Tuple[float, float]] = {}
    for node, (x, y) in pos.items():
        name = getattr(node, "name", None) or str(node)
        result[name] = (float(x), float(y))
    return result


def _simple_fallback(
    nodes: List[Any], algorithm: str = "grid", **kwargs
) -> Dict[Any, Tuple[float, float]]:
    """Fallback simple layouts: grid or circular."""
    n = len(nodes)
    if n == 0:
        return {}

    pos = {}
    if algorithm == "circular":
        import math

        radius = kwargs.get("radius", max(100, 40 * n))
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / n
            pos[node] = (radius * math.cos(angle), radius * math.sin(angle))
    else:
        # grid
        cols = int(kwargs.get("cols", max(1, int(n**0.5))))
        spacing = kwargs.get("spacing", 150)
        for i, node in enumerate(nodes):
            r = i // cols
            c = i % cols
            pos[node] = (c * spacing, r * spacing)

    return pos
