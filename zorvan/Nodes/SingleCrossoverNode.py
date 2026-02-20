import random

from zorvan.Nodes.BasicNode import BasicNode


class SingleCrossoverNode(BasicNode):
    def __init__(self, name: str = "", value=None):
        super().__init__(name, value)  # Call the parent BasicNode constructor
        self.batchSize = 2
        self.crossoverRate = 0.9
        self.delay = 1
        self.iterationCount = 0

    def Operation(self, p1, p2):
        """
        Perform Crossover on the given inputs. Return the first side Crossover.
        """
        if self.iterationCount >= self.delay:
            if random.random() > self.crossoverRate:
                return p1[:], p2[:]
            point = random.randint(1, len(p1) - 2)
            self.iterationCount = 0
            return p1[:point] + p2[point:]
        else:
            self.iterationCount += 1

    def IsValidInput(self, inp):
        """
        Check if the input is valid for multiplication (must be a number).
        """
        return isinstance(inp, (int, float, list, tuple))
