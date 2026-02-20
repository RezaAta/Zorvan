import numpy as np

from zorvan.Nodes.BasicNode import BasicNode
from zorvan.Nodes.SigmoidDerivativeNode import SigmoidDerivativeNode


class SigmoidNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.inputCount = 1
        self.batchSize = 1
        self.inclusive = False
        self.derivative = SigmoidDerivativeNode

    def Operation(self, x):
        return 1 / (1 + np.exp(-x))

    def IsValidInput(self, inp):
        """
        Check if the input is valid for sigmoid (must be a number, including numpy types).
        """
        return isinstance(inp, (int, float, np.integer, np.floating))
