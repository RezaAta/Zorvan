from ComputationalGraphs.Nodes.BasicNode import BasicNode
import random

class BulkTournamentNode(BasicNode):
    def __init__(self, name: str = "", value = None, tournamentSize: int = 3, 
                 populationSize: int = 30, num_selections: int = None):
        """
        Bulk tournament selection node.
        
        Args:
            name: Node name
            value: Initial value
            tournamentSize: Number of individuals in each tournament
            populationSize: Size of the population to collect before selecting
            num_selections: Number of individuals to select (defaults to populationSize)
                           Set to populationSize-1 when using elitism to maintain pop size
        """
        super().__init__(name, value)  # Call the parent BasicNode constructor
        self.inputCount = 2  # Default input count for the multiplication node
        self.tournamentSize = tournamentSize
        self.populationSize = populationSize
        # If num_selections not specified, select same as population size (no elitism)
        self.num_selections = num_selections if num_selections is not None else populationSize
        self.population = []
        self.selected = []
        self.fitnesses = []
        self.iteration = 0
        self.batchSize = 2

    def Operation(self, candidate, fitness):
        if len(self.selected) > 0:
            selectedCandidate = self.selected.pop()
            if len(self.selected) == 0:
                self.population.clear()
                self.fitnesses.clear()
            return selectedCandidate
        else:
            if candidate is not None and fitness is not None:
                self.population.append(candidate)
                self.fitnesses.append(fitness)
            
            if len(self.population) == self.populationSize:
                # Perform tournament selection for num_selections individuals
                self.selected = []
                for _ in range(self.num_selections):
                    candidates = random.sample(list(zip(self.population, self.fitnesses)), self.tournamentSize)
                    winner = min(candidates, key=lambda x: x[1])[0]
                    self.selected.append(winner)
                
                return self.selected[-1]
            return None
    

    def IsValidInput(self, inp):
        """
        Check if the input is valid for multiplication (must be a number).
        """
        # return isinstance(inp, (int, float, list))
        return True
