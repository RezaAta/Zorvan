from abc import ABC, abstractmethod

from ComputationalGraphs.Nodes.AbstractNode import AbstractNode
from ComputationalGraphs.Nodes.Node import Node


# BasicNode class (Abstract)
class BasicNode(Node, ABC):  # Inherits from both Node and ABC
    def __init__(self, name: str, value=0):
        super().__init__(name)  # Call Node's constructor
        self.value = value  # Node's value
        self.inputCount = 0  # Number of inputs
        self.computationType = "basic"  # Type of computation for the node

    def ResetValue(self):
        import logging
        import traceback

        # Preserve user-edited values when flagged
        if getattr(self, "user_locked_value", False):
            logging.getLogger(__name__).debug(
                "ResetValue skipped for %s because user_locked_value=True",
                getattr(self, "name", str(self)),
            )
            return
        logging.getLogger(__name__).debug(
            "ResetValue: resetting %s (previous value=%s)\n%s",
            getattr(self, "name", str(self)),
            getattr(self, "value", None),
            "\n".join(traceback.format_stack()),
        )
        self.value = 0

    # Computation-structure/time helpers removed (unused). If needed later, reintroduce with tests.

    @abstractmethod
    def Operation(self, inputs):
        """Perform the basic node's operation. To be defined by subclasses."""
        pass

    def UpdateInputs(self):
        """Update the inputs array with the valid values of predecessor nodes."""
        # Be defensive: if inputs was accidentally set to a non-list (e.g., a string),
        # reset it to an empty list instead of calling .clear() on an object
        # that may not support it.
        if not isinstance(self.inputs, list):
            self.inputs = []
        else:
            try:
                self.inputs.clear()
            except Exception:
                self.inputs = []

        # Fetch values from predecessors and only store valid inputs
        for predecessor in self.predecessors:
            if isinstance(predecessor, AbstractNode):
                predecessor.UpdateValues()
                for value in predecessor.value:
                    if self.IsValidInput(value):
                        self.inputs.append(value)
            else:
                value = predecessor.value
                if self.IsValidInput(value):
                    self.inputs.append(value)

    @abstractmethod
    def IsValidInput(self, inp):
        """Check if an input is valid. Must be overridden by subclasses."""
        pass
