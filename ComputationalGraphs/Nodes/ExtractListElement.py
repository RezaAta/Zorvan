from ComputationalGraphs.Nodes.BasicNode import BasicNode


# BasicNode class (Abstract)
class ExtractListElement(BasicNode):  # Inherits from both Node and ABC
    def __init__(self, name: str = "", index=0, value=None):
        super().__init__(name, value)  # Call Node's constructor
        self.inputCount = 1  # Number of inputs
        self.batchSize = 1  # Number of inputs
        self.index = index
        self.computationType = "basic"  # Type of computation for the node
        self.inclusive = False

    def Operation(self, input):
        if input is not None and isinstance(input, list):
            return input[self.index]
        else:
            return None

    def IsValidInput(self, input):
        return True
