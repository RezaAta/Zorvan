from zorvan.Nodes.BasicNode import BasicNode


class SequencerNode(BasicNode):
    def __init__(self, name: str = "", data=None):
        super().__init__(name, 0)
        self.buffer = data if data else []  # Start with given data or an empty list
        self.value = self.buffer[0] if self.buffer else None
        self.batchSize = 1
        self.inclusive = False
        self.forcedBatchProcessing = True

    def ResetValue(self):
        if not isinstance(self.buffer, list):
            self.buffer = []
        else:
            try:
                self.buffer.clear()
            except Exception:
                self.buffer = []
        if not getattr(self, "user_locked_value", False):
            self.value = 0

    # This node can take multiple inputs, streamline them inside a buffer, and output them one by one in each iteration.
    def Operation(self, input):
        # if input is not None:
        if not self.midCalculation and not len(self.buffer) == 0:
            self.buffer.pop(0)

        if input is not None:
            # If input is a list of lists (multiple genomes/individuals), extend to add each
            # If input is a single list (one genome/individual) or other type, append as-is
            if (
                isinstance(input, list)
                and len(input) > 0
                and isinstance(input[0], list)
            ):
                # List of lists - extend to add each individual
                self.buffer.extend(input)
            else:
                # Single item (could be a genome, which is a list) - append as single unit
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
        if not isinstance(self.buffer, list):
            self.buffer = []
        else:
            try:
                self.buffer.clear()
            except Exception:
                self.buffer = []
        if not getattr(self, "user_locked_value", False):
            self.value = None
