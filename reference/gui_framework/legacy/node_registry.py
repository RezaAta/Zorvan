"""
Central registry for node categories used by palettes and dialogs.

Provides a single authoritative copy of available node categories and a
helper to include dynamically-registered custom nodes.
"""

from copy import deepcopy

# Static base categories (copied from legacy NodePalette definition)
NODE_CATEGORIES = {
    "Basic Operations": {
        "description": "Fundamental arithmetic operations",
        "nodes": [
            ("AdditionNode", "Addition", "Adds multiple input values"),
            (
                "SubtractionNode",
                "Subtraction",
                "Subtracts second input from first",
            ),
            ("MultiplicationNode", "Multiplication", "Multiplies input values"),
            ("DivisionNode", "Division", "Divides first input by second"),
        ],
    },
    "Data & Buffers": {
        "description": "Data sources and storage containers",
        "nodes": [
            ("DataStreamNode", "Data Stream", "Provides sequential data from a source"),
            (
                "DynamicDataStreamNode",
                "Dynamic Data Stream",
                "Dynamic data source with runtime updates",
            ),
            ("BufferNode", "Buffer", "Stores and manages recent values"),
            (
                "MovingAverageNode",
                "Moving Average",
                "Calculates average of buffered values (continuous or batch mode)",
            ),
            ("SequencerNode", "Sequencer", "Sequences multiple inputs"),
            ("ListNode", "List", "Collects inputs into a list structure"),
            ("ContainerNode", "Container", "General-purpose data container"),
            (
                "InitializableContainerNode",
                "Container (Init)",
                "Container node with initializable/random value (weights)",
            ),
            (
                "ExtractListElement",
                "Extract List Element",
                "Extracts element from list by index",
            ),
        ],
    },
    "Activation Functions": {
        "description": "Neural network activation functions",
        "nodes": [
            ("SigmoidNode", "Sigmoid", "Sigmoid activation function"),
            ("SigmoidDerivativeNode", "Sigmoid'", "Derivative of sigmoid function"),
            ("ReLUNode", "ReLU", "Rectified Linear Unit activation"),
            ("ReLUDerivativeNode", "ReLU'", "Derivative of ReLU function"),
            ("LinearNode", "Linear", "Linear activation (identity)"),
            ("LinearNodeDerivative", "Linear'", "Derivative of linear function"),
            ("TanhNode", "Tanh", "Hyperbolic tangent activation function"),
            (
                "TanhDerivativeNode",
                "Tanh'",
                "Derivative of hyperbolic tangent function",
            ),
            ("GaussianNode", "Gaussian", "Gaussian (bell curve) function"),
            ("PiecewiseLinearNode", "Piecewise Linear", "Piecewise linear function"),
        ],
    },
    "Loss Functions": {
        "description": "Error and loss calculations (buffer-style)",
        "nodes": [
            (
                "MeanSquaredNode",
                "MS",
                "Buffer-based Mean Squared (mean of squared buffered values). Single-input node; supports continuous or batch modes.",
            ),
        ],
    },
    "Statistical": {
        "description": "Statistical operations and aggregations",
        "nodes": [
            ("MaxNode", "Maximum", "Returns the maximum value from inputs"),
            ("MinNode", "Minimum", "Returns the minimum value from inputs"),
        ],
    },
    "Evolutionary Algorithms": {
        "description": "Genetic algorithm and optimization nodes",
        "nodes": [
            ("PopulationNode", "Population", "Auto-generating GA population node"),
            (
                "TournamentSelectionNode",
                "Tournament Selection",
                "Selects best individuals via tournament",
            ),
            (
                "BulkTournamentNode",
                "Bulk Tournament",
                "Bulk tournament selection operation",
            ),
            ("CrossoverNode", "Crossover", "Genetic crossover of two individuals"),
            (
                "SingleCrossoverNode",
                "Single Crossover",
                "Single-point crossover operation",
            ),
            (
                "SingleInputCrossover",
                "Single Input Crossover",
                "Crossover with single input",
            ),
            ("MutationNode", "Mutation", "Random genetic mutation"),
            ("ElitismNode", "Elitism", "Preserves best individual across generations"),
            ("DeJongSphereNode", "De Jong Sphere", "De Jong sphere fitness function"),
        ],
    },
    "Utility Nodes": {
        "description": "Utility and I/O nodes",
        "nodes": [
            ("DisplayNode", "Display", "Prints values to console or log"),
        ],
    },
}


def get_node_categories():
    """Return a fresh copy of categories including any custom nodes.

    This function pulls custom node definitions from the custom node manager
    so runtime-added nodes appear under a "Custom Nodes" category.
    """
    cats = deepcopy(NODE_CATEGORIES)
    try:
        from gui_framework.legacy.custom_node_manager import get_custom_node_manager

        manager = get_custom_node_manager()
        custom_types = manager.get_type_names()
        if custom_types:
            cats.setdefault(
                "Custom Nodes",
                {"description": "User-defined custom nodes", "nodes": []},
            )
            cats["Custom Nodes"]["nodes"] = [
                (type_name, type_name, manager.get_definition(type_name).description)
                for type_name in custom_types
            ]
    except Exception:
        # If custom node manager is unavailable, silently continue
        pass
    return cats
