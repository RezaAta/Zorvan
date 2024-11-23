from BasicNode import BasicNode

class MeanSquaredErrorNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.value = None
        self.inclusive = False

    def Operation(self, predicted, target):
        squared_error = (predicted - target) ** 2
        if self.value is None:
            return squared_error
        else:
            # return (squared_error + self.value) / 2
            return squared_error


    def IsValidInput(self, inp):
        """Check if the input is a valid number (int or float)."""
        return isinstance(inp, (int, float))
