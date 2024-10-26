from abc import ABC, abstractmethod
from Node import Node
from AbstractNode import AbstractNode

# BasicNode class (Abstract)
class BasicNode(Node, ABC):  # Inherits from both Node and ABC
    def __init__(self, name: str, value=0):
        super().__init__(name)  # Call Node's constructor
        self.value = value  # Node's value
        self.inputCount = 0  # Number of inputs
        self.computationType = 'basic'  # Type of computation for the node

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
        self.inputs = []  # Clear previous inputs
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

    def ProcessBatch(self):
        """
        Process the next batch of inputs. If `inclusive` is True, the node's new value
        is appended to the inputs at the beginning and used in the next batch.
        If the number of inputs is less than `batchSize`, finish the calculation early.
        """
        if self.midCalculation:
            # Insert the node's value at the start of the inputs if inclusive
            if self.inclusive:
                self.inputs.insert(0, self.value)

            # Check if there are enough inputs to process a batch
            if len(self.inputs) < self.batchSize:
                self.midCalculation = False  # Not enough inputs, finish calculation
                return

            # Process the batch
            batch = self.inputs[:self.batchSize]
            self.value = self.Operation(*batch)
            self.inputs = self.inputs[self.batchSize:]  # Remove processed inputs

            if not self.inputs:
                self.midCalculation = False  # Finished processing all inputs
        else:
            # Start processing the first batch
            if self.inputs:
                # Check if there are enough inputs to process a batch
                if len(self.inputs) < self.batchSize:
                    self.midCalculation = False  # Not enough inputs, finish calculation
                    return

                batch = self.inputs[:self.batchSize]
                self.value = self.Operation(*batch)
                self.inputs = self.inputs[self.batchSize:]  # Remove processed inputs

                if self.inputs:
                    self.midCalculation = True  # Set mid-calculation for remaining inputs
