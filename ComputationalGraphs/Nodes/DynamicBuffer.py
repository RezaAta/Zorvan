from ComputationalGraphs.Nodes.BasicNode import BasicNode

class DynamicBuffer(BasicNode):
    def __init__(self, name: str = "", data=None):
        super().__init__(name, 0)
        self.buffer = data if data else []  # Start with given data or an empty list
        self.value = self.buffer[0] if self.buffer else None
        self.batchSize = 1
        self.inclusive = False
        self.forcedBatchProcessing = True

    def ResetValue(self):
        self.buffer.clear()
        self.value = 0

    def Operation(self, input):
        # if input is not None:
        if not self.midCalculation and not len(self.buffer) == 0:
            self.buffer.pop(0)
        
        if input is not None:
            self.buffer.append(input)
    
        if len(self.buffer) == 0:
            return None
        else:
            return self.buffer[0]  # Set value to the oldest element

        # else:
        #     return None
        
    def IsValidInput(self, input):
        return True


    def ResetBuffer(self):
        """Clear the buffer for fresh computations."""
        self.buffer.clear()
        self.value = None

    