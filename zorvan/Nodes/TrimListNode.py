from zorvan.Nodes.BasicNode import BasicNode

# Diagnostics counters
TRIM_CALLS = 0
TRIM_NONNONE = 0


class TrimListNode(BasicNode):
    """Trim a list to a specified maximum length.

    Returns the input list truncated to `max_len` elements. If input is not a list,
    returns it unchanged.
    """

    def __init__(self, name: str = "", max_len: int = None, value=None):
        super().__init__(name, value)
        self.max_len = max_len
        self.inputCount = 1
        self.batchSize = 1

    def Operation(self, input):
        global TRIM_CALLS, TRIM_NONNONE
        TRIM_CALLS += 1
        if input is not None:
            TRIM_NONNONE += 1
        if isinstance(input, list) and self.max_len is not None:
            return input[: self.max_len]
        return input

    def IsValidInput(self, input):
        return True
