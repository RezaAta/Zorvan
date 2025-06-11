from ComputationalGraphs.Nodes.BasicNode import BasicNode

class MaxNode(BasicNode):
    def __init__(self, name: str = ""):
        super().__init__(name=name, value=0.0)
        self.inputCount = 2
        self.forcedBatchProcessing = True

    def Operation(self, a:float, b:float ) -> float:
        
        return float(max([a,b]))

    def IsValidInput(self, inp) -> bool:
        return isinstance(inp, (int, float))

