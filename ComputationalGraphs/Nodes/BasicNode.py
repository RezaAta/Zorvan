from abc import ABC, abstractmethod
from ComputationalGraphs.Nodes.Node import Node
from ComputationalGraphs.Nodes.AbstractNode import AbstractNode

# BasicNode class (Abstract)
class BasicNode(Node, ABC):  # Inherits from both Node and ABC
    def __init__(self, name: str, value=0):
        super().__init__(name)  # Call Node's constructor
        self.value = value  # Node's value
        self.inputCount = 0  # Number of inputs
        self.computationType = 'basic'  # Type of computation for the node

    def ResetValue(self):
        self.value = 0

    def SetComputationStructure(self):
        self.computationStructure = self.id  # If no nodes are present, return an empty string

    def UpdateComputationTime(self):
        self.computationTime = 1

    @abstractmethod
    def Operation(self, inputs):
        """Perform the basic node's operation. To be defined by subclasses."""
        pass

    def UpdateInputs(self):
        """Update the inputs array with the valid values of predecessor nodes."""
        self.inputs.clear()  # Clear previous inputs
        # Fetch values from predecessors and only store valid inputs
        for predecessor in self.predecessors:
            if isinstance(predecessor, AbstractNode):
                predecessor.UpdateValues()
                for value in predecessor.value:
                    if self.IsValidInput(value):
                        self.inputs.append(value)
            else:
                value = predecessor.value
                if self.IsValidInput(value):
                    self.inputs.append(value)

    @abstractmethod
    def IsValidInput(self, inp):
        """Check if an input is valid. Must be overridden by subclasses."""
        pass
