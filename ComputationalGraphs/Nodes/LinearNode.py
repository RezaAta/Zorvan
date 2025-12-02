from ComputationalGraphs.Nodes.BasicNode import BasicNode
from ComputationalGraphs.Nodes.LinearNodeDerivative import LinearNodeDerivative


# BasicNode class (Abstract)
class LinearNode(BasicNode):  # Inherits from both Node and ABC
    def __init__(self, name: str = "", value: float = 0):
        super().__init__(name, value)  # Call Node's constructor
        self.inputCount = 1  # Number of inputs
        self.batchSize = 1  # Number of inputs
        self.computationType = "basic"  # Type of computation for the node
        self.inclusive = False
        self.derivative = LinearNodeDerivative

    def Operation(self, input):
        return input

    def IsValidInput(self, input):
        import numpy as np

        return isinstance(input, (int, float, np.integer, np.floating))
