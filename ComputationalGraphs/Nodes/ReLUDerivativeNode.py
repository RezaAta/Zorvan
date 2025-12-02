from ComputationalGraphs.Nodes.BasicNode import BasicNode


class ReLUDerivativeNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.inputCount = 1
        self.batchSize = 1
        self.inclusive = False

    def Operation(self, ReLUOutput):
        if ReLUOutput > 0:
            return 1
        else:
            return 0

    def IsValidInput(self, inp):
        """
        Check if the input is valid for multiplication (must be a number).
        """
        return isinstance(inp, (int, float))
