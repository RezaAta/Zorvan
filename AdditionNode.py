from BasicNode import BasicNode

class AdditionNode(BasicNode):
    def __init__(self, id: str, value=0):
        super().__init__(id, value)
        self.inputCount = 2  # Set how many inputs the addition node expects
        self.batchSize = 2
        self.inclusive = False

    def Operation(self, a, b):
        """
        Perform Sum on the given inputs. Ensure inputs length matches inputCount.
        """
        return a + b

    def IsValidInput(self, input):
        """Check if inputs are valid for addition (e.g., must be numbers)."""

        return isinstance(input, (int, float))
