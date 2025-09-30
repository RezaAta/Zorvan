from ComputationalGraphs.Nodes.BasicNode import BasicNode
import random

class MutaionNode(BasicNode):
    def __init__(self, name: str = "", value = 0, rate:float = 0.5, scale: float = 0.1):
        super().__init__(name, value)  # Call the parent BasicNode constructor
        self.batchSize = 1
        self.scale = scale
        self.rate = rate

    def Operation(self, inp):
        if isinstance(inp, (int, float, list, tuple)):
            return [gene + random.gauss(0, self.scale) if random.random() < self.rate else gene for gene in inp]
        else:
            return None
    def IsValidInput(self, inp):
        return True

