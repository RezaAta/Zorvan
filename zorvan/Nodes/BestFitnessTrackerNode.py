from zorvan.Nodes.BasicNode import BasicNode


class BestFitnessTrackerNode(BasicNode):
    """
    Tracks the best fitness value for each generation in an evolutionary algorithm.

    This node collects fitness values across a generation and keeps track of the
    best (minimum) fitness from each generation to create a fitness history.

    Inputs:
        1. Individual (genome) - not used, just for synchronization
        2. Fitness value

    Args:
        population_size: Number of individuals per generation
    """

    def __init__(self, name: str = "", population_size: int = 10, value=None):
        super().__init__(name, value)
        self.inputCount = 2  # individual, fitness
        self.batchSize = 2
        self.population_size = population_size

        # Track best fitness per generation
        self.best_fitness_history = []
        self.current_generation_fitnesses = []
        self.individuals_seen = 0

    def Operation(self, individual, fitness):
        """
        Collects fitness values and tracks best per generation.

        Args:
            individual: The genome (not used, just for sync)
            fitness: The fitness value

        Returns:
            The best fitness seen so far in current generation
        """
        # Skip None inputs
        if individual is None or fitness is None:
            return None

        # Add fitness to current generation
        self.current_generation_fitnesses.append(fitness)
        self.individuals_seen += 1

        # Check if generation is complete
        if self.individuals_seen >= self.population_size:
            # Find and store best fitness from this generation
            if self.current_generation_fitnesses:
                best_fitness = min(self.current_generation_fitnesses)
                self.best_fitness_history.append(best_fitness)

            # Reset for next generation
            if not isinstance(self.current_generation_fitnesses, list):
                self.current_generation_fitnesses = []
            else:
                try:
                    self.current_generation_fitnesses.clear()
                except Exception:
                    self.current_generation_fitnesses = []
            self.individuals_seen = 0

        # Return current best in this generation (or None if no data yet)
        if self.current_generation_fitnesses:
            return min(self.current_generation_fitnesses)
        return None

    def ResetTracker(self):
        """Reset tracking (call between runs)."""
        if not isinstance(self.best_fitness_history, list):
            self.best_fitness_history = []
        else:
            try:
                self.best_fitness_history.clear()
            except Exception:
                self.best_fitness_history = []
        if not isinstance(self.current_generation_fitnesses, list):
            self.current_generation_fitnesses = []
        else:
            try:
                self.current_generation_fitnesses.clear()
            except Exception:
                self.current_generation_fitnesses = []
        self.individuals_seen = 0

    def IsValidInput(self, inp):
        """Accept any input type."""
        return True
