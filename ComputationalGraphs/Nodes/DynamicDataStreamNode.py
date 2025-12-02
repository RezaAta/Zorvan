from ComputationalGraphs.Nodes.BasicNode import BasicNode


class DynamicDataStreamNode(BasicNode):
    def __init__(
        self, name: str = "", data=[], initialDelay: int = 0, streamDelay: int = 0
    ):
        super().__init__(name, 0)
        self.initialDelay = initialDelay
        self.streamDelay = streamDelay
        self.iteration = 0
        self.lastStream = 0
        self.data = data
        self.streamIndex = 0
        if data:  # Ensure data list is non-empty before accessing
            self.value = data[0]
        else:
            self.value = None  # Default to None if data is empty

    def ResetValue(self):
        self.data = None
        self.iteration = 0
        self.lastStream = 0

    def Operation(self, input):
        if input is not None:
            self.data.append(input)
        if self.initialDelay - self.iteration <= 0:
            if self.iteration - self.lastStream >= self.streamDelay:
                self.streamIndex += 1
                if self.streamIndex >= len(self.data):
                    self.streamIndex = 0  # Loop back to the start
                self.value = self.data[self.streamIndex]
                self.lastStream = self.iteration
        self.iteration += 1

    def IsValidInput(self, inp):
        pass
