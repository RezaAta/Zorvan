import math
from ComputationalGraphs.Nodes.BasicNode import BasicNode


class GaussianMembershipNode(BasicNode):
    """Gaussian membership function that takes three predecessors:
    (input_value, center_container, sigma_container)
    Both center and sigma are expected to be numeric nodes (e.g., `ContainerNode`)
    so they can be adjusted externally without modifying this node implementation.
    """
    def __init__(self, name: str = "", default_center: float = 0.0, default_sigma: float = 1.0):
        super().__init__(name=name, value=0.0)
        # This node expects 3 predecessors: input, center, sigma
        self.inputCount = 3
        self.batchSize = 3

    def Operation(self, x: float, c: float, s: float) -> float:
        try:
            xv = float(x)
            cv = float(c)
            sv = float(s)
        except Exception:
            return 0.0

        # Avoid division by zero / negative sigma
        sv = max(abs(sv), 1e-6)
        return math.exp(-((xv - cv) ** 2) / (2.0 * (sv ** 2)))

    def IsValidInput(self, inp) -> bool:
        return isinstance(inp, (int, float))
