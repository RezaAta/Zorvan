from abc import ABC, abstractmethod
from Node import Node

# BasicNode class (Abstract)
class BasicNode(Node, ABC):  # Inherits from both Node and ABC
    def __init__(self, name: str, value=0):
        super().__init__(name)  # Call Node's constructor
        self.value = value  # Node's value
        self.inputCount = 0  # Number of inputs
        self.computationType = 'basic'  # Type of computation for the node

    @abstractmethod
    def Operation(self, inputs):
        """Perform the basic node's operation. To be defined by subclasses."""
        pass

    @abstractmethod
    def IsValidInput(self, inputs):
        """Check if the inputs are valid. To be defined by subclasses."""
        pass
