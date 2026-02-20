from zorvan.Nodes.BasicNode import BasicNode
from zorvan.Nodes.ReLUDerivativeNode import ReLUDerivativeNode


class ReLUNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.inputCount = 1
        self.batchSize = 1
        self.inclusive = False
        self.derivative = ReLUDerivativeNode

    def Operation(self, x):
        return max(0, x)

    def IsValidInput(self, inp):
        if isinstance(inp, (float, int)):
            return True
        else:
            return False
