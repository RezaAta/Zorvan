import random

from ComputationalGraphs.Nodes.BasicNode import BasicNode


# BasicNode class (Abstract)
class CrossoverNode(BasicNode):  # Inherits from both Node and ABC
    def __init__(
        self, name: str = "", rate: float = 0.9, value: int = None, delay: int = 1
    ):
        super().__init__(name, value)  # Call Node's constructor
        self.inputCount = 2  # Number of inputs
        self.batchSize = 2  # Number of inputs
        self.delay = delay
        self.iteration = 0
        self.computationType = "basic"  # Type of computation for the node
        self.inclusive = False
        self.rate = rate

    def Operation(self, p1, p2):
        if self.iteration >= self.delay:
            self.iteration = 0
            if random.random() > self.rate:
                return p1[:], p2[:]
            point = random.randint(1, len(p1) - 1)
            return [p1[:point] + p2[point:], p2[:point] + p1[point:]]
        else:
            self.iteration += 1

    def IsValidInput(self, input):
        """Check if the inputs are valid. To be defined by subclasses."""
        if input is not None and isinstance(input, list):
            return True
        else:
            return False
