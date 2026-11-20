"""Initializers for Container/Initializable nodes.

This module provides a small, backward-compatible set of initializer classes so
that `InitializableContainerNode` can import and use them. The API is tiny:

- class Initializer: abstract base, implement `generate()`
- class UniformInitializer(Initializer): returns random.uniform(low, high)
- class NormalInitializer(Initializer): returns random.gauss(mean, std)

The project previously expected an `Initializer` class to exist in this
package; creating this minimal implementation restores compatibility.
"""

from __future__ import annotations

import random
from typing import Optional


class Initializer:
    """Abstract base initializer.

    Subclasses should implement `generate()` and accept configuration via
    their constructor. This keeps the API intentionally simple.
    """

    def generate(self) -> float:
        """Return a generated float value.

        Raise NotImplementedError in the base class so callers have a clear
        error if a concrete initializer has not been provided.
        """
        raise NotImplementedError(
            "Initializer.generate() must be implemented by subclasses"
        )


class UniformInitializer(Initializer):
    def __init__(self, low: float = -1.0, high: float = 1.0):
        self.low = low
        self.high = high

    def generate(self) -> float:
        return random.uniform(self.low, self.high)


class NormalInitializer(Initializer):
    def __init__(self, mean: float = 0.0, std: float = 1.0):
        self.mean = mean
        self.std = std

    def generate(self) -> float:
        # Uses Gaussian (normal) distribution
        return random.gauss(self.mean, self.std)
