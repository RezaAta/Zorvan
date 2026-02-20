from zorvan.Nodes.BasicNode import BasicNode


class DeJongSphereNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)  # Call the parent BasicNode constructor
        self.batchSize = 1

    def Operation(self, input):
        return sum(i**2 for i in input)

    def IsValidInput(self, inp):
        return isinstance(inp, list) and all(isinstance(i, (int, float)) for i in inp)
