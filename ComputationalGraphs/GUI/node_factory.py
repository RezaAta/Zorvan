"""
Node factory helper for creating nodes by type string.

Refactored to use a dictionary-based registry pattern for cleaner code
and easier extensibility.
"""

from typing import Any, Dict, Optional, Type

# Registry mapping node type names to (module_path, class_name, default_kwargs, name_prefix)
_NODE_REGISTRY: Dict[str, tuple] = {
    # Data nodes
    "DataStreamNode": (
        "ComputationalGraphs.Nodes.DataStreamNode",
        "DataStreamNode",
        {"data": [1, 2, 3, 4, 5]},
        "Data",
    ),
    "DynamicDataStreamNode": (
        "ComputationalGraphs.Nodes.DynamicDataStreamNode",
        "DynamicDataStreamNode",
        {},
        "DynData",
    ),
    "BufferNode": (
        "ComputationalGraphs.Nodes.BufferNode",
        "BufferNode",
        {"size": 3},
        "Buffer",
    ),
    "MovingAverageNode": (
        "ComputationalGraphs.Nodes.MovingAverageNode",
        "MovingAverageNode",
        {"size": 10, "mode": "continuous"},
        "MovAvg",
    ),
    "SequencerNode": (
        "ComputationalGraphs.Nodes.SequencerNode",
        "SequencerNode",
        {},
        "Seq",
    ),
    "ListNode": ("ComputationalGraphs.Nodes.ListNode", "ListNode", {}, "List"),
    "ExtractListElement": (
        "ComputationalGraphs.Nodes.ExtractListElement",
        "ExtractListElement",
        {"index": 0},
        "ExtractList",
    ),
    "ContainerNode": (
        "ComputationalGraphs.Nodes.ContainerNode",
        "ContainerNode",
        {},
        "Container",
    ),
    # Arithmetic nodes
    "AdditionNode": (
        "ComputationalGraphs.Nodes.AdditionNode",
        "AdditionNode",
        {},
        "Add",
    ),
    "SubtractionNode": (
        "ComputationalGraphs.Nodes.SubtractionNode",
        "SubtractionNode",
        {},
        "Sub",
    ),
    "MultiplicationNode": (
        "ComputationalGraphs.Nodes.MultiplicationNode",
        "MultiplicationNode",
        {},
        "Mul",
    ),
    "DivisionNode": (
        "ComputationalGraphs.Nodes.DivisionNode",
        "DivisionNode",
        {},
        "Div",
    ),
    "MaxNode": ("ComputationalGraphs.Nodes.MaxNode", "MaxNode", {}, "Max"),
    "MinNode": ("ComputationalGraphs.Nodes.MinNode", "MinNode", {}, "Min"),
    "MeanSquaredNode": (
        "ComputationalGraphs.Nodes.MeanSquaredNode",
        "MeanSquaredNode",
        {},
        "MS",
    ),
    # Activation functions
    "SigmoidNode": (
        "ComputationalGraphs.Nodes.SigmoidNode",
        "SigmoidNode",
        {},
        "Sigmoid",
    ),
    "SigmoidDerivativeNode": (
        "ComputationalGraphs.Nodes.SigmoidDerivativeNode",
        "SigmoidDerivativeNode",
        {},
        "Sigmoid'",
    ),
    "ReLUNode": ("ComputationalGraphs.Nodes.ReLUNode", "ReLUNode", {}, "ReLU"),
    "ReLUDerivativeNode": (
        "ComputationalGraphs.Nodes.ReLUDerivativeNode",
        "ReLUDerivativeNode",
        {},
        "ReLU'",
    ),
    "LinearNode": ("ComputationalGraphs.Nodes.LinearNode", "LinearNode", {}, "Linear"),
    "TanhNode": ("ComputationalGraphs.Nodes.TanhNode", "TanhNode", {}, "Tanh"),
    "TanhDerivativeNode": (
        "ComputationalGraphs.Nodes.TanhDerivativeNode",
        "TanhDerivativeNode",
        {},
        "Tanh'",
    ),
    "GaussianNode": (
        "ComputationalGraphs.Nodes.GaussianNode",
        "GaussianNode",
        {},
        "Gauss",
    ),
    "PiecewiseLinearNode": (
        "ComputationalGraphs.Nodes.PiecewiseLinearNode",
        "PiecewiseLinearNode",
        {},
        "Piecewise",
    ),
    # Evolutionary algorithm nodes
    "TournamentSelectionNode": (
        "ComputationalGraphs.Nodes.TournamentSelectionNode",
        "TournamentSelectionNode",
        {},
        "Tournament",
    ),
    "BulkTournamentNode": (
        "ComputationalGraphs.Nodes.BulkTournamentNode",
        "BulkTournamentNode",
        {},
        "BulkTour",
    ),
    "CrossoverNode": (
        "ComputationalGraphs.Nodes.CrossoverNode",
        "CrossoverNode",
        {},
        "Crossover",
    ),
    "SingleCrossoverNode": (
        "ComputationalGraphs.Nodes.SingleCrossoverNode",
        "SingleCrossoverNode",
        {},
        "SingleXO",
    ),
    "MutationNode": (
        "ComputationalGraphs.Nodes.MutationNode",
        "MutaionNode",
        {},
        "Mutation",
    ),  # Note: typo preserved from original class
    "DeJongSphereNode": (
        "ComputationalGraphs.Nodes.DeJongSphereNode",
        "DeJongSphereNode",
        {},
        "DeJong",
    ),
    # Utility nodes
    "DisplayNode": (
        "ComputationalGraphs.Nodes.DisplayNode",
        "DisplayNode",
        {},
        "Display",
    ),
}

# Cache for imported classes
_CLASS_CACHE: Dict[str, Type] = {}


def _import_node_class(node_type: str) -> Optional[Type]:
    """Import and cache a node class by type name.

    Args:
        node_type: The node type string from the registry

    Returns:
        The node class, or None if not found
    """
    if node_type in _CLASS_CACHE:
        return _CLASS_CACHE[node_type]

    if node_type not in _NODE_REGISTRY:
        return None

    module_path, class_name, _, _ = _NODE_REGISTRY[node_type]

    # Special case: custom node marked with "__custom__" module path
    if module_path == "__custom__":
        try:
            from ComputationalGraphs.GUI.custom_node_manager import (
                get_custom_node_manager,
            )

            manager = get_custom_node_manager()
            cls = manager.get_node_class(node_type)
            if cls:
                _CLASS_CACHE[node_type] = cls
            return cls
        except Exception:
            return None

    try:
        import importlib

        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        _CLASS_CACHE[node_type] = cls
        return cls
    except (ImportError, AttributeError):
        return None


def create_node(node_type: str, name_hint: Optional[str] = None):
    """Return a new instance of a node for node_type.

    The function returns None if node_type is unknown.

    Args:
        node_type: The type of node to create (e.g., "AdditionNode")
        name_hint: Optional name hint for the node (used as suffix)

    Returns:
        A new node instance, or None if type is unknown
    """
    if node_type not in _NODE_REGISTRY:
        return None

    cls = _import_node_class(node_type)
    if cls is None:
        return None

    # Get default kwargs and name prefix
    _, _, default_kwargs, name_prefix = _NODE_REGISTRY[node_type]
    base_name = name_hint or "Node"

    # Build kwargs with name
    kwargs = {"name": f"{name_prefix}_{base_name}"}
    kwargs.update(default_kwargs)

    try:
        return cls(**kwargs)
    except Exception:
        return None


def get_available_node_types() -> list:
    """Return a list of all registered node type names.

    Returns:
        List of node type strings
    """
    return list(_NODE_REGISTRY.keys())


def register_node_type(
    node_type: str,
    module_path: str,
    class_name: str,
    default_kwargs: Optional[Dict[str, Any]] = None,
    name_prefix: Optional[str] = None,
):
    """Register a new node type for factory creation.

    This allows extending the factory with custom node types.

    Args:
        node_type: The type name to register (e.g., "MyCustomNode")
        module_path: Full module path (e.g., "mypackage.nodes.MyNode")
        class_name: Class name within the module
        default_kwargs: Default keyword arguments for instantiation
        name_prefix: Prefix for auto-generated names
    """
    prefix = name_prefix or node_type.replace("Node", "")
    _NODE_REGISTRY[node_type] = (module_path, class_name, default_kwargs or {}, prefix)
