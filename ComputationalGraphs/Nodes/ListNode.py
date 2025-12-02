from ComputationalGraphs.Nodes.BasicNode import BasicNode


# ...existing code...
class ListNode(BasicNode):
    def __init__(self, name: str = "", allowNone: bool = False):
        super().__init__(name, 0)
        self.value = []
        self.batchSize = 1
        self.forcedBatchProcessing = True
        self.inclusive = False
        self.allowNone = allowNone
        self._invalid_batch = False  # new flag to track invalidation within a timestep

    def Operation(self, input):
        # start fresh at the beginning of a batch
        if self.midCalculation is False:
            self.value = []
            self._invalid_batch = False

        # if a previous input already invalidated this batch, keep returning None
        if self._invalid_batch:
            return None

        # if None values are not allowed, invalidate the whole output for this timestep
        if not self.allowNone and input is None:
            self.value = None
            self._invalid_batch = True
            return None

        # otherwise append and return the accumulating list
        if self.value is None:
            self.value = []
        self.value.append(input)
        return self.value

    def IsValidInput(self, input):
        return True
