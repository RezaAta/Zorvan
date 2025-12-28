from ComputationalGraphs.Nodes.BasicNode import BasicNode


class AdditionNode(BasicNode):
    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.inputCount = 2  # Set how many inputs the addition node expects
        self.batchSize = 2
        self.inclusive = True

    def Operation(self, a, b):
        """
        Perform Sum on the given inputs. Ensure inputs length matches inputCount.
        """
        return a + b

    def IsValidInput(self, input):
        """
        Check if inputs are valid for addition (must be numbers, including numpy types).
        """
        import numpy as np

        return isinstance(input, (int, float, np.integer, np.floating))

    def ProcessBatch(self):
        if (len(self.inputs) == 1) and (self.midCalculation is False):
            # Avoid overwriting user-edited value during automatic processing
            if not getattr(self, "user_locked_value", False):
                self.value = self.Operation(0, self.inputs[0])
            else:
                try:
                    import logging

                    logging.getLogger(__name__).debug(
                        "Preserving user-locked value for %s in AdditionNode.ProcessBatch",
                        getattr(self, "name", str(self)),
                    )
                except Exception:
                    pass
        else:
            return super().ProcessBatch()
