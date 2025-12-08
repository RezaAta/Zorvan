"""InitializableContainerNode - extension of ContainerNode with reinitialization support.
"""

import random
from typing import Optional

from ComputationalGraphs.Nodes.ContainerNode import ContainerNode


class InitializableContainerNode(ContainerNode):
    """A ContainerNode that supports random initialization / re-initialization.

    Thin subclass of ContainerNode that adds init range parameters and a
    convenience method `reinitialize` to randomize the node's value.
    """

    def __init__(
        self,
        name: str = "",
        value: float = 0.0,
        init_low: float = -1.0,
        init_high: float = 1.0,
        init_method: str = "uniform",
        init_mean: float = 0.0,
        init_std: float = 0.01,
    ):
        super().__init__(name=name, value=value)
        self.init_low = init_low
        self.init_high = init_high
        self.init_method = init_method
        self.init_mean = init_mean
        self.init_std = init_std

    def reinitialize(self) -> float:
        """Randomize this node's value using the configured init method.

        Supports 'uniform' currently; more methods can be added later.
        Returns the newly set value.
        """
        if self.init_method == "uniform":
            self.value = random.uniform(self.init_low, self.init_high)
        elif self.init_method == "normal":
            # Clip if desired to keep in range, but base functionality returns gaussian
            self.value = random.gauss(self.init_mean, self.init_std)
        # Removed 'zeros', 'ones', 'constant' modes - these were redundant
        else:
            # Fallback: uniform
            self.value = random.uniform(self.init_low, self.init_high)
        return self.value
