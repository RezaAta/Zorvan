from BasicNode import BasicNode

class SigmoidDerivativeNode(BasicNode):
    def __init__(self, name: str = "", value = 0):
        super().__init__(name, value)
        self.inputCount = 1
        self.batchSize = 1
        self.inclusive = False

    def Operation(self, sigmoid_output):
        """
        Compute the derivative of the sigmoid function given its output.
        """
        return sigmoid_output * (1 - sigmoid_output)

    def IsValidInput(self, inp):
        """
        Check if the input is valid for the operation (must be a number).
        """
        return isinstance(inp, (int, float))
