from abc import ABC, abstractmethod


class Node(ABC):
    def __init__(self, name: str, inclusive=True, forcedBatchProcessing=False):
        self.name = name
        self.predecessors = []  # List of predecessor nodes
        self.inputs = []  # Store the inputs to be processed
        self.value = 0.0  # Initial value of the node
        self.midCalculation = False  # Tracks if node is mid-calculation
        self.midCalculationValue = 0
        self.batchSize = 2  # Set batch size to 2 for this example
        self.inclusive = inclusive  # Determines if node's result is added to next batch
        self.forcedBatchProcessing = forcedBatchProcessing  # Enable forced processing

    @abstractmethod
    def Operation(self, *inputs):
        """Perform the node's operation on the given inputs."""
        pass

    def AddPreNode(self, *predecessors):
        """Add a predecessor node to this node."""
        for predecessor in predecessors:
            if predecessor not in self.predecessors:
                self.predecessors.append(predecessor)

    def UpdateInputs(self):
        """Update the inputs array with the valid values of predecessor nodes."""
        # Use list comprehension for better performance than loop with append
        self.inputs = [
            predecessor.value
            for predecessor in self.predecessors
            if self.IsValidInput(predecessor.value)
        ]

    def ProcessBatch(self):
        """
        Process inputs in batches. If `inclusive` is True, add the node's current value
        to the start of each batch. If `forcedBatchProcessing` is enabled, continue processing
        until there are insufficient inputs.
        """
        while True:
            if self.midCalculation:
                # Insert the node's value at the start of inputs if inclusive
                if self.inclusive:
                    self.inputs.insert(0, self.midCalculationValue)

                # Check if there are enough inputs to process a batch
                if len(self.inputs) < self.batchSize:
                    self.midCalculation = False
                    self.value = self.midCalculationValue
                    break

                # Process the batch
                batch = self.inputs[: self.batchSize]
                self.midCalculationValue = self.Operation(*batch)
                self.inputs = self.inputs[self.batchSize :]  # Remove processed inputs

                if not self.inputs:
                    self.midCalculation = False  # Finished processing all inputs
                    self.value = self.midCalculationValue
                    break

            else:
                if len(self.inputs) < self.batchSize:
                    self.midCalculation = False  # Not enough inputs to start
                    break

                # Start processing the first batch
                batch = self.inputs[: self.batchSize]
                self.midCalculationValue = self.Operation(*batch)
                self.inputs = self.inputs[self.batchSize :]  # Remove processed inputs

                if self.inputs:
                    self.midCalculation = (
                        True  # Set mid-calculation for remaining inputs
                    )
                else:
                    self.value = self.midCalculationValue
                    break

            # Break if not forcing batch processing
            if not self.forcedBatchProcessing:
                break
