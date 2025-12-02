import numpy as np

from ComputationalGraphs.Nodes.BasicNode import BasicNode
from ComputationalGraphs.Nodes.TanhDerivativeNode import TanhDerivativeNode


class TanhNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.inputCount = 1
        self.batchSize = 1
        self.inclusive = False
        self.derivative = TanhDerivativeNode

    def Operation(self, x):
        return np.tanh(x)

    def IsValidInput(self, inp):
        """
        Check if the input is valid for tanh (must be a number, including numpy types).
        """
        return isinstance(inp, (int, float, np.integer, np.floating))
