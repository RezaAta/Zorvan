from BasicNode import BasicNode

class DataStreamNode(BasicNode):
    def __init__(self, name: str = "", data = [], size = 1, initialDelay: int = 0, streamDelay: int = 0):
        super().__init__(name, 0)
        self.buffer = data
        if len(data) > size:
            print("Buffer Overloaded! Extending Buffer.")
            self.bufferSize = len(data)
        else:
            self.bufferSize = size

        if data:  # Ensure data list is non-empty before accessing
            self.value = data[0]
        else:
            self.value = None  # Default to None if data is empty

        self.batchSize = 1
        self.inclusive = False

    def Operation(self, input):
        self.buffer.append(input)
        if len(self.buffer) > self.bufferSize:
            self.buffer.pop(0)

        self.value = self.buffer[0]

    def IsValidInput(self, inp):
        pass

