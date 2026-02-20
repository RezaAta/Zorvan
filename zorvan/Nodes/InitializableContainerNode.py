import random
from typing import Optional

from zorvan.Nodes.ContainerNode import ContainerNode
from zorvan.Nodes.Initializers.Initializer import Initializer


class InitializableContainerNode(ContainerNode):
    """A ContainerNode that supports random initialization / re-initialization.

    This is a thin subclass of ContainerNode that adds parameters for the
    initialization range and a convenience method ``reinitialize`` to assign
    a new random value to the node.
    """

    def __init__(
        self,
        name: str = "",
        value: float = 0.0,
        init_low: float = -1.0,
        init_high: float = 1.0,
        init_mean: float = 0.0,
        init_std: float = 1.0,
        init_method: str = "uniform",
        initializer: Optional[Initializer] = None,
    ):
        # Keep underlying ContainerNode behavior
        super().__init__(name=name, value=value)
        # Initialization params (support both uniform and normal methods)
        self.init_low = init_low
        self.init_high = init_high
        self.init_mean = init_mean
        self.init_std = init_std
        self.init_method = init_method
        # optional initializer object
        self.initializer = initializer

    def reinitialize(self) -> float:
        """Randomize this node's value using the configured init method.

        Currently supports 'uniform' only. Returns the new value.
        """
        if self.initializer is not None:
            try:
                self.value = self.initializer.generate()
            except Exception:
                # fall back to internal uniform logic
                self.value = random.uniform(self.init_low, self.init_high)
        elif self.init_method == "uniform":
            self.value = random.uniform(self.init_low, self.init_high)
        elif self.init_method == "normal":
            # Use normal distribution with configured mean/std
            try:
                self.value = random.normalvariate(self.init_mean, self.init_std)
            except Exception:
                # fall back to uniform if something goes wrong
                self.value = random.uniform(self.init_low, self.init_high)
        else:
            # fallback to uniform if unknown method
            self.value = random.uniform(self.init_low, self.init_high)

        return self.value

    # Keep Operation inherited from ContainerNode; that preserves backprop semantics

    def set_initializer(self, initializer: Initializer):
        """Set an initializer object and return it."""
        self.initializer = initializer
        return self.initializer

    def regenerate_value(self):
        """Compatibility alias for other code that expects regenerate_value()"""
        return self.reinitialize()
