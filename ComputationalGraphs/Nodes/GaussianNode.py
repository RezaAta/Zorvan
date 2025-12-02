import numpy as np

from ComputationalGraphs.Nodes.BasicNode import BasicNode


class GaussianNode(BasicNode):
    def __init__(
        self,
        name: str = "",
        mean: float = 0.0,
        sigma: float = 1.0,
        amplitude: float = 1.0,
    ):
        super().__init__(name)
        self.mean = mean
        self.sigma = sigma
        self.amplitude = amplitude
        self.inputCount = 1
        self.computationType = "fuzzification"

    def Operation(self, input_value):
        """
        Applies the Gaussian membership function with amplitude to the input value.
        μ(x) = amplitude * exp(-((x - mean)^2) / (2 * sigma^2))
        """
        return self.amplitude * np.exp(
            -((input_value - self.mean) ** 2) / (2 * self.sigma**2)
        )

    def IsValidInput(self, input_value):
        """
        Validates the input. For Gaussian membership functions, any real number is valid.
        """
        return isinstance(input_value, (int, float, np.number))
