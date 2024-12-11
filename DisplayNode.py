from BasicNode import BasicNode
from DisplayNodeDerivative import DisplayNodeDerivative

# BasicNode class (Abstract)
class DisplayNode(BasicNode):  # Inherits from both Node and ABC
    def __init__(self, name: str = "", value: int = 0):
        super().__init__(name, value)  # Call Node's constructor
        self.inputCount = 1  # Number of inputs
        self.batchSize = 1  # Number of inputs
        self.computationType = 'basic'  # Type of computation for the node
        self.inclusive = False
        self.derivative = DisplayNodeDerivative

    def Operation(self, input):
        return input

    def IsValidInput(self, input):
        """Check if the inputs are valid. To be defined by subclasses."""
        if input is not None:
            return True
        else:
            return False
