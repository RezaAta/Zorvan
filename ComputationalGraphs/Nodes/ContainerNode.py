from ComputationalGraphs.Nodes.BasicNode import BasicNode


class ContainerNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.inputCount = 2  # Set how many inputs the addition node expects
        self.batchSize = 1
        self.inclusive = False
        self.Incremental = False

    def Operation(self, i):
        """
        Perform Sum on the given inputs. Ensure inputs length matches inputCount.
        """
        if self.Incremental:
            return self.value + i
        else:
            return self.value - i

    def IsValidInput(self, input):
        """
        Check if inputs are valid for addition (e.g., must be numbers).
        """
        return isinstance(input, (int, float))
