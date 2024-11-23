from BasicNode import BasicNode

class BufferNode(BasicNode):
    def __init__(self, name: str = "", data=None, size: int = 1):
        super().__init__(name, 0)
        self.buffer = data if data else []  # Start with given data or an empty list
        self.bufferSize = max(size, len(self.buffer))  # Set buffer size based on max of size or initial data length
        self.value = self.buffer[0] if self.buffer else None
        self.batchSize = 1
        self.inclusive = False

    def Operation(self, input):
        """Add new input to buffer and maintain size constraint."""
        self.buffer.append(input)
        if len(self.buffer) > self.bufferSize:
            self.buffer.pop(0)
        if len(self.buffer) == 0:
            return None
        else:
            return self.buffer[0]  # Set value to the oldest element

    def IsValidInput(self, input):
        return True

    def ResetBuffer(self):
        """Clear the buffer for fresh computations."""
        self.buffer.clear()
        self.value = None
