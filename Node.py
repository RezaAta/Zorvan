from abc import ABC, abstractmethod

class Node(ABC):
    def __init__(self, name: str, inclusive=True):
        self.name = name
        self.predecessors = []  # List of predecessor nodes
        self.inputs = []        # Store the inputs to be processed
        self.value = 0.0        # Initial value of the node
        self.midCalculation = False  # Tracks if node is mid-calculation
        self.midCalculationValue = 0
        self.batchSize = 2  # Set batch size to 2 to match your node's logic
        self.inclusive = inclusive  # Determines if node's result is added to next batch

    @abstractmethod
    def Operation(self, *inputs):
        """Perform the node's operation on the given inputs."""
        pass

    def AddPreNode(self, predecessor):
        """Add a predecessor node to this node."""
        if predecessor not in self.predecessors:
            self.predecessors.append(predecessor)

    def UpdateInputs(self):
        """Update the inputs array with the valid values of predecessor nodes."""
        self.inputs = []  # Clear previous inputs
        # Fetch values from predecessors and only store valid inputs
        for predecessor in self.predecessors:
            value = predecessor.value
            if self.IsValidInput(value):
                self.inputs.append(value)

    def ProcessBatch(self):
        """
        Process the next batch of inputs. If `inclusive` is True, the node's new value
        is appended to the inputs at the beginning and used in the next batch.
        If the number of inputs is less than `batchSize`, finish the calculation early.
        """
        if self.midCalculation:
            # Insert the node's value at the start of the inputs if inclusive
            if self.inclusive:
                self.inputs.insert(0, self.midCalculationValue)

            # Check if there are enough inputs to process a batch
            if len(self.inputs) < self.batchSize:
                self.midCalculation = False  # Not enough inputs, finish calculation
                self.value = self.midCalculationValue
                return

            # Process the batch
            batch = self.inputs[:self.batchSize]
            self.midCalculationValue = self.Operation(*batch)
            self.inputs = self.inputs[self.batchSize:]  # Remove processed inputs

            if not self.inputs:
                self.midCalculation = False  # Finished processing all inputs
                self.value = self.midCalculationValue
        else:
            # Start processing the first batch
            if self.inputs:
                # Check if there are enough inputs to process a batch
                if len(self.inputs) < self.batchSize:
                    self.midCalculation = False  # Not enough inputs, finish calculation
                    return

                batch = self.inputs[:self.batchSize]
                self.midCalculationValue = self.Operation(*batch)
                self.inputs = self.inputs[self.batchSize:]  # Remove processed inputs

                if self.inputs:
                    self.midCalculation = True  # Set mid-calculation for remaining inputs
                else:
                    self.value = self.midCalculationValue
