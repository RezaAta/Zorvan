from ComputationalGraphs.Nodes.BasicNode import BasicNode
from copy import deepcopy
from typing import Any

class BufferNode(BasicNode):
    def __init__(self, name: str = "", data=None, size: int = 1, allowNone: bool = True):
        super().__init__(name, 0)
        self.buffer = list(data) if data is not None else [None] * size  # Start with given data or a list of None of length size
        self.bufferSize = max(size, len(self.buffer))  # Set buffer size based on max of size or initial data length
        self.value = self.buffer[0] if self.buffer else None
        self.batchSize = 1
        self.inclusive = False
        self.allowNone = allowNone  # If False, None values will be discarded

    def ResetValue(self):
        self.buffer.clear()
        self.value = None

    def Operation(self, input):
        """Add new input to buffer and maintain size constraint."""
        # Normalize numpy scalar types to native Python types where possible
        item = input
        try:
            import numpy as _np
            # np.ndarray (0-d) or np.generic convert to Python scalar
            if isinstance(input, _np.ndarray):
                # zero-d arrays -> item(), else keep array
                if input.shape == ():
                    item = input.item()
            elif isinstance(input, _np.generic):
                item = input.item()
        except Exception:
            # numpy not available or conversion failed; fall back to original input
            item = input

        # If allowNone is False and input is None, skip adding to buffer
        if not self.allowNone and item is None:
            # Return current oldest element without modifying buffer
            if len(self.buffer) == 0:
                return None
            else:
                for it in self.buffer:
                    if it is not None:
                        return it
                return None  # All items are None

        # Add input to buffer (including None if allowNone is True)
        item = deepcopy(item)
        self.buffer.append(item)
        if len(self.buffer) > self.bufferSize:
            self.buffer.pop(0)

        if len(self.buffer) == 0:
            return None
        else:
            # If allowNone is False, skip None values in output too
            if not self.allowNone:
                # Find first non-None value in buffer
                for item in self.buffer:
                    if item is not None:
                        return item
                return None  # All items are None
            else:
                return self.buffer[0]  # Set value to the oldest element

    def IsValidInput(self, input):
        return True

    def ResetBuffer(self):
        """Clear the buffer for fresh computations."""
        self.buffer.clear()
        self.value = None
