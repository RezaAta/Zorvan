from ComputationalGraphs.Nodes.BasicNode import BasicNode


class MinNode(BasicNode):
    def __init__(self, name: str = ""):
        super().__init__(name=name, value=0.0)
        self.inputCount = 2
        self.forcedBatchProcessing = True

    def Operation(self, a: float, b: float) -> float:

        return float(min([a, b]))

    def IsValidInput(self, inp) -> bool:
        return isinstance(inp, (int, float))
