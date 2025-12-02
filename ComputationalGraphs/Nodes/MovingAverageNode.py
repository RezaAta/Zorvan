from copy import deepcopy

from ComputationalGraphs.Nodes.BufferNode import BufferNode


class MovingAverageNode(BufferNode):
    """
    A buffer-based node that calculates the average of stored values.

    Two modes:
    1. 'continuous': Recalculates average every iteration (true moving average)
    2. 'batch': Waits for buffer to fill completely, calculates average, then waits
       for full buffer replacement before recalculating (batch average)

    Behaves exactly like BufferNode but outputs the average instead of the oldest value.
    """

    def __init__(
        self,
        name: str = "",
        data=None,
        size: int = 10,
        mode="continuous",
        allowNone: bool = False,
    ):
        """
        Initialize MovingAverageNode.

        Args:
            name: Node identifier
            data: Initial data to populate buffer
            size: Buffer capacity (number of values to store)
            mode: 'continuous' or 'batch'
                - 'continuous': Update average every iteration
                - 'batch': Update average only when buffer is fully replaced
            allowNone: If False, None values will be discarded
        """
        # Initialize parent BufferNode
        super().__init__(name=name, data=data, size=size, allowNone=allowNone)
        self.mode = mode
        self.values_since_last_update = 0  # Track replacements in batch mode

        # Initialize value to 0.0 (will be updated as data comes in)
        self.value = 0.0

        # Calculate initial average if data was provided
        if data is not None:
            self._update_average()

    def Operation(self, input):
        """
        Store input value in buffer and calculate average based on mode.

        Args:
            input: Single input value to add to buffer

        Returns:
            float: Average of buffer contents (updated based on mode)
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
            return self.value  # Return current average

        # Add input to buffer using parent's logic
        item = deepcopy(item)
        self.buffer.append(item)
        if len(self.buffer) > self.bufferSize:
            self.buffer.pop(0)

        # Calculate and return average
        return self._update_average()

    def _update_average(self):
        """Calculate average based on mode and return it."""
        # Filter out None values for averaging
        valid_values = [v for v in self.buffer if v is not None]

        if len(valid_values) == 0:
            # No valid values, keep current value
            return self.value if hasattr(self, "value") else 0.0

        # Calculate the new average
        new_average = float(sum(valid_values) / len(valid_values))

        # Update self.value based on mode
        if self.mode == "continuous":
            # Continuous mode: update every iteration
            self.value = new_average

        elif self.mode == "batch":
            # Batch mode: only update when buffer is fully replaced
            self.values_since_last_update += 1

            # Check if buffer is full and all values have been replaced
            if (
                len(self.buffer) >= self.bufferSize
                and self.values_since_last_update >= self.bufferSize
            ):
                # Update to new average
                self.value = new_average
                # Reset replacement counter
                self.values_since_last_update = 0

        # Always return the calculated average (not self.value in batch mode)
        return new_average

    def ResetBuffer(self):
        """Reset buffer and state."""
        super().ResetBuffer()
        self.values_since_last_update = 0
        self.value = 0.0

    def __repr__(self):
        valid_count = len([v for v in self.buffer if v is not None])
        return f"MovingAverageNode('{self.name}', size={self.bufferSize}, mode='{self.mode}', avg={self.value:.4f}, buffer_fill={valid_count}/{self.bufferSize})"
