from abc import ABC, abstractmethod

class Node(ABC):
    def __init__(self, name: str = "", inclusive=True):
        self.name = name
        self.id = ""
        self.predecessors = []  # List of predecessor nodes
        self.inputs = []        # Store the inputs to be processed
        self.value = 0.0        # Initial value of the node
        self.midCalculation = False  # Tracks if node is mid-calculation
        self.batchSize = 2  # Set batch size to 2 to match your node's logic
        self.inclusive = inclusive  # Determines if node's result is added to next batch
        self.computationTime = 1

    @abstractmethod
    def Operation(self, *inputs):
        """Perform the node's operation on the given inputs."""
        pass

    def AddPreNode(self, predecessor):
        """Add a predecessor node to this node."""
        self.predecessors.append(predecessor)