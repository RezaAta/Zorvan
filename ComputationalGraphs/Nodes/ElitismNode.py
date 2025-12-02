from ComputationalGraphs.Nodes.BasicNode import BasicNode


class ElitismNode(BasicNode):
    """
    Implements elitism for genetic algorithms.
    Keeps track of the best N individuals from the current generation and outputs them
    only when the generation is complete.

    This node takes two inputs:
    1. Individual (genome/chromosome)
    2. Fitness value

    It buffers all individuals and their fitnesses for a generation, then outputs
    the best N individuals when the generation completes.

    Args:
        num_elites: Number of best individuals to preserve (default 1)
    """

    def __init__(
        self, name: str = "", population_size: int = 10, num_elites: int = 1, value=None
    ):
        super().__init__(name, value)
        self.inputCount = 2  # individual, fitness
        self.batchSize = 2
        self.population_size = population_size
        self.num_elites = max(1, min(num_elites, population_size))  # Ensure valid range

        # Generation tracking
        self.individuals_buffer = []
        self.fitnesses_buffer = []
        self.elite_individuals = []
        self.elite_fitnesses = []

        # Counter for generation completion
        self.individuals_collected = 0

    def Operation(self, individual, fitness):
        """
        Collects individuals and fitnesses, outputs best N when generation completes.

        Args:
            individual: The genome/chromosome
            fitness: The fitness value for this individual

        Returns:
            List of best N individuals when generation completes, None otherwise
        """
        # Skip None inputs
        if individual is None or fitness is None:
            return None

        # Add to buffers
        self.individuals_buffer.append(individual)
        self.fitnesses_buffer.append(fitness)
        self.individuals_collected += 1

        # Check if generation is complete
        if self.individuals_collected >= self.population_size:
            # Generation complete - find best N individuals
            # Sort by fitness (assuming minimization)
            sorted_pairs = sorted(
                zip(self.fitnesses_buffer, self.individuals_buffer), key=lambda x: x[0]
            )

            # Extract top N individuals
            self.elite_individuals = [ind for _, ind in sorted_pairs[: self.num_elites]]
            self.elite_fitnesses = [fit for fit, _ in sorted_pairs[: self.num_elites]]

            # Reset for next generation
            self.individuals_buffer.clear()
            self.fitnesses_buffer.clear()
            self.individuals_collected = 0

            # Always return a list of elite individuals
            # This ensures SequencerNode can properly extend the list
            return self.elite_individuals
        else:
            # Generation not complete yet - return None
            return None

    def ResetElitism(self):
        """Reset elitism tracking (call between runs)."""
        self.individuals_buffer.clear()
        self.fitnesses_buffer.clear()
        self.elite_individuals.clear()
        self.elite_fitnesses.clear()
        self.individuals_collected = 0

    def GetBestFitness(self):
        """Get the fitness of the best elite individual."""
        if self.elite_fitnesses:
            return self.elite_fitnesses[0]  # Already sorted, first is best
        return None

    def IsValidInput(self, inp):
        """Accept any input type."""
        return True
