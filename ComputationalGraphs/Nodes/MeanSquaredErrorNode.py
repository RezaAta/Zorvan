from copy import deepcopy

from ComputationalGraphs.Nodes.MovingAverageNode import MovingAverageNode


class MeanSquaredErrorNode(MovingAverageNode):
    """
    MeanSquaredErrorNode behaves exactly like MovingAverageNode but computes
    the mean of squared values stored in the buffer (i.e. mean(x^2) over the buffer)
    rather than the arithmetic mean.

    This class deliberately copies MovingAverageNode's API and behaviour
    (including `mode`, `allowNone`, buffer sizing and `Operation(self, input)` signature)
    so it can be used interchangeably where a moving-average-like buffer node is expected.
    """

    def __init__(
        self,
        name: str = "",
        data=None,
        size: int = 10,
        mode="continuous",
        allowNone: bool = False,
    ):
        super().__init__(
            name=name, data=data, size=size, mode=mode, allowNone=allowNone
        )

        # Initialize value to 0.0 (MovingAverageNode already does this, but ensure consistency)
        self.value = 0.0

        # If initial data provided, compute initial MSE
        if data is not None:
            self._update_mse()

    def Operation(self, input):
        """
        Accepts a single input (mirrors MovingAverageNode signature).
        Appends the input to the buffer and returns the mean squared value
        across the buffer (MSE relative to zero).
        """
        # Normalize numpy scalar types to native Python types where possible
        item = input
        try:
            import numpy as _np

            if isinstance(input, _np.ndarray):
                if input.shape == ():
                    item = input.item()
            elif isinstance(input, _np.generic):
                item = input.item()
        except Exception:
            item = input

        # If allowNone is False and input is None, skip
        if not self.allowNone and item is None:
            return self.value

        # Add input to buffer using parent's logic
        item = deepcopy(item)
        self.buffer.append(item)
        if len(self.buffer) > self.bufferSize:
            self.buffer.pop(0)

        # Calculate and return MSE
        return self._update_mse()

    def _update_mse(self):
        """Calculate mean squared value based on mode and return it."""
        # Filter out None values
        valid_values = [v for v in self.buffer if v is not None]

        if len(valid_values) == 0:
            return self.value if hasattr(self, "value") else 0.0

        # Mean of squared values
        new_mse = float(sum((v**2 for v in valid_values)) / len(valid_values))

        # Update value depending on mode
        if self.mode == "continuous":
            self.value = new_mse
        elif self.mode == "batch":
            self.values_since_last_update += 1
            if (
                len(self.buffer) >= self.bufferSize
                and self.values_since_last_update >= self.bufferSize
            ):
                self.value = new_mse
                self.values_since_last_update = 0

        # Return computed MSE (not necessarily self.value in batch mode)
        return new_mse

    def ResetBuffer(self):
        """Reset buffer and state (mirror MovingAverageNode)."""
        super().ResetBuffer()
        self.values_since_last_update = 0
        self.value = 0.0

    def __repr__(self):
        valid_count = len([v for v in self.buffer if v is not None])
        return f"MeanSquaredErrorNode('{self.name}', size={self.bufferSize}, mode='{self.mode}', mse={self.value:.6f}, buffer_fill={valid_count}/{self.bufferSize})"
