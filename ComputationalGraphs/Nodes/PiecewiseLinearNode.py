import numpy as np

from ComputationalGraphs.Nodes.BasicNode import BasicNode


class PiecewiseLinearNode(BasicNode):
    """
    Piecewise‐linear membership function node (strict < / > checks).
    xs: strictly increasing support points [x0, x1, …, xn]
    mus: membership values at those points [μ0, μ1, …, μn]
    For x < x0 or x > xn: returns 0.0.
    If x == xi exactly: returns μi.
    Otherwise linearly interpolates between adjacent knots.
    """

    def __init__(
        self,
        name: str = "",
        xs: list[float] = [0, 50, 100],
        mus: list[float] = [0.0, 0.5, 1.0],
    ):
        super().__init__(name=name, value=0.0)
        assert len(xs) == len(mus) >= 2, "Need at least two support points"
        sorted_pairs = sorted(zip(xs, mus), key=lambda p: p[0])
        self.xs = np.array([pt for pt, _ in sorted_pairs], dtype=float)
        self.mus = np.array([mv for _, mv in sorted_pairs], dtype=float)
        self.inputCount = 1
        self.batchSize = 1

    def Operation(self, x: float) -> float:
        x_val = float(x)
        # Outside the support => 0.0
        if x_val < self.xs[0] or x_val > self.xs[-1]:
            return 0.0

        # Exact match to a knot?
        idx_exact = np.where(np.isclose(self.xs, x_val))[0]
        if idx_exact.size > 0:
            return float(self.mus[idx_exact[0]])

        # Find interval [i0, i1] so that xs[i0] < x < xs[i1]
        pos = np.searchsorted(self.xs, x_val)
        i0 = pos - 1
        i1 = pos
        x0, x1 = self.xs[i0], self.xs[i1]
        mu0, mu1 = self.mus[i0], self.mus[i1]

        # Linear interpolation
        return float(mu0 + (mu1 - mu0) * (x_val - x0) / (x1 - x0))

    def IsValidInput(self, inp) -> bool:
        return isinstance(inp, (int, float, np.floating, np.integer))
