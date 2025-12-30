import random

from ComputationalGraphs.Nodes.BasicNode import BasicNode

# BasicNode class (Abstract)
# Debugging counters (incremented when children are produced)
CHILDREN_PRODUCED = 0


class SingleInputCrossover(BasicNode):  # Inherits from both Node and ABC
    def __init__(
        self, name: str = "", rate: float = 0.9, value: int = None, delay: int = 0
    ):
        super().__init__(name, value)  # Call Node's constructor
        self.inputCount = 1  # Number of inputs
        self.batchSize = 1  # Number of inputs
        self.delay = delay
        self.iteration = 0
        self.selectedPopulation = []
        self.computationType = "basic"  # Type of computation for the node
        self.inclusive = False
        self.rate = rate

    def Operation(self, p):
        global CHILDREN_PRODUCED
        if p is not None and isinstance(p, list):
            if self.iteration >= self.delay:
                self.iteration = 0
                self.selectedPopulation.append(p)
                if len(self.selectedPopulation) >= 2:
                    p1 = self.selectedPopulation[0]
                    p2 = self.selectedPopulation[1]
                    if not isinstance(self.selectedPopulation, list):
                        self.selectedPopulation = []
                    else:
                        try:
                            self.selectedPopulation.clear()
                        except Exception:
                            self.selectedPopulation = []
                    if random.random() > self.rate:
                        CHILDREN_PRODUCED += 2
                        return [p1[:], p2[:]]
                    # Use the actual parent length, ensure it's valid
                    parent_len = len(p1)
                    if parent_len < 2:
                        # If genome is too short, just return copies
                        CHILDREN_PRODUCED += 2
                        return [p1[:], p2[:]]
                    point = random.randint(1, parent_len - 1)
                    CHILDREN_PRODUCED += 2
                    return [p1[:point] + p2[point:], p2[:point] + p1[point:]]

                else:
                    return None

            else:
                self.iteration += 1
                return None

        else:
            return None

    def IsValidInput(self, inp):
        return True
