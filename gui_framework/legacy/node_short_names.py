"""Shared mapping for short node names used by canvas and palettes."""

NODE_SHORT_NAMES = {
    # Data nodes
    "DataStreamNode": "Data",
    "DynamicDataStreamNode": "DynData",
    "BufferNode": "Buffer",
    "MovingAverageNode": "MovAvg",
    "SequencerNode": "Seq",
    "ListNode": "List",
    "ExtractListElement": "Extract",
    "ContainerNode": "Container",
    # Arithmetic nodes
    "AdditionNode": "Add",
    "SubtractionNode": "Sub",
    "MultiplicationNode": "Mul",
    "DivisionNode": "Div",
    # Statistical nodes
    "MaxNode": "Max",
    "MinNode": "Min",
    "MeanSquaredNode": "MS",
    # Activation functions
    "SigmoidNode": "Sigmoid",
    "SigmoidDerivativeNode": "Sigmoid'",
    "ReLUNode": "ReLU",
    "ReLUDerivativeNode": "ReLU'",
    "LinearNode": "Linear",
    "TanhNode": "Tanh",
    "TanhDerivativeNode": "Tanh'",
    "GaussianNode": "Gauss",
    "PiecewiseLinearNode": "Piecewise",
    # Evolutionary algorithm nodes
    "TournamentSelectionNode": "Tournament",
    "BulkTournamentNode": "BulkTour",
    "CrossoverNode": "Crossover",
    "SingleCrossoverNode": "SingleXO",
    "MutationNode": "Mutation",
    "DeJongSphereNode": "DeJong",
    # Utility nodes
    "DisplayNode": "Display",
    "InitializableContainerNode": "InitC",
    "LinearNodeDerivative": "Linear'",
    "PopulationNode": "Pop",
    "SingleInputCrossover": "SInXO",
}


def get_short_name(class_name: str) -> str:
    """Return short name for a node class name, or the original if not found."""
    return NODE_SHORT_NAMES.get(class_name, class_name)
