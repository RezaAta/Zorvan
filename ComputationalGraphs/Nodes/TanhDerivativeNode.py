from ComputationalGraphs.Nodes.BasicNode import BasicNode


class TanhDerivativeNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.inputCount = 1
        self.batchSize = 1
        self.inclusive = False

    def Operation(self, tanh_output):
        """
        Compute the derivative of tanh given its output.
        derivative = 1 - tanh(x)^2 -> using tanh output directly
        """
        return 1 - (tanh_output ** 2)

    def IsValidInput(self, inp):
        """
        Check if the input is valid for the operation (must be a number, including numpy types).
        """
        import numpy as np
        return isinstance(inp, (int, float, np.integer, np.floating))
