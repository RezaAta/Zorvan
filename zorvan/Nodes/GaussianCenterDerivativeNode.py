import math

from zorvan.Nodes.BasicNode import BasicNode


class GaussianCenterDerivativeNode(BasicNode):
    """Computes derivative of Gaussian MF wrt center c: dmu/dc = mu * (x - c) / (s^2)

    Expects predecessors: (x, c, s) and returns scalar.
    """

    def __init__(self, name: str = ""):
        super().__init__(name=name, value=0.0)
        self.inputCount = 3
        self.batchSize = 3

    def Operation(self, x, c, s):
        try:
            xv = float(x)
            cv = float(c)
            sv = float(s)
        except Exception:
            return 0.0

        sv = max(abs(sv), 1e-6)
        mu = math.exp(-((xv - cv) ** 2) / (2.0 * (sv**2)))
        return mu * (xv - cv) / (sv**2)

    def IsValidInput(self, inp) -> bool:
        return isinstance(inp, (int, float))
