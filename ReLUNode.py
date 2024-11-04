from BasicNode import BasicNode

class ReLUNode(BasicNode):
    def __init__(self, name: str, value = 0):
        super().__init__(name, value)
        self.inputCount = 1
        self.inclusive = False

    def Operation(self, x):
        return max(0, x)
    def IsValidInput(self, inp):
        if isinstance(inp, (float, int)):
            return True
        else:
            return False