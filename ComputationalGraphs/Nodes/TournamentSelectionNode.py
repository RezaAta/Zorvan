from ComputationalGraphs.Nodes.BasicNode import BasicNode

class TournamentSelectionNode(BasicNode):
    def __init__(self, name: str = "", value = None, tournamentSize:int = 3):
        super().__init__(name, value)  # Call the parent BasicNode constructor
        self.inputCount = 2  # Default input count for the multiplication node
        self.tournamentSize = tournamentSize
        self.candidates = []
        self.fitnesses = []
        self.iteration = 0
        self.batchSize = 2

    def Operation(self, candidate, fitness):
        self.candidates.append(candidate)
        self.fitnesses.append(fitness)
        
        if len(self.candidates) >= self.tournamentSize:
            minFitness = min(self.fitnesses)
            index = self.fitnesses.index(minFitness)

            winner = self.candidates[index]
            self.candidates.clear()
            self.fitnesses.clear()
            return winner
        else: 
            return None
    

    def IsValidInput(self, inp):
        """
        Check if the input is valid for multiplication (must be a number).
        """
        return isinstance(inp, (int, float, list))
