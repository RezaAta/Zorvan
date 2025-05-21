from ComputationalGraphs.Nodes.BasicNode import BasicNode

class SubtractionNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.inputCount = 2  # Set how many inputs the addition node expects
        self.batchSize = 2
        self.inclusive = True

    def Operation(self, a, b):
        return a - b

    def IsValidInput(self, input):
        """
        Check if inputs are valid for addition (e.g., must be numbers).
        """
        return isinstance(input, (int, float))
    def ProcessBatch(self):
        if (len(self.inputs) == 1) and (self.midCalculation is False):
            self.value = self.Operation(0,self.inputs[0])
        else:
            return super().ProcessBatch()
