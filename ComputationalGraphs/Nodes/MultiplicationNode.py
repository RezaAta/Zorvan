from ComputationalGraphs.Nodes.BasicNode import BasicNode

class MultiplicationNode(BasicNode):
    def __init__(self, name: str = "", value = 0):
        super().__init__(name, value)  # Call the parent BasicNode constructor
        self.inputCount = 2  # Default input count for the multiplication node
        self.batchSize = 2

    def Operation(self, a,b):
        """
        Perform multiplication on the given inputs. Ensure inputs length matches inputCount.
        """
        return a*b

    def IsValidInput(self, inp):
        """
        Check if the input is valid for multiplication (must be a number, including numpy types).
        """
        import numpy as np
        return isinstance(inp, (int, float, np.integer, np.floating))
