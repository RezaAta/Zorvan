from ComputationalGraphs.Nodes.BufferNode import BufferNode
import random

class PopulationNode(BufferNode):
    """
    A specialized BufferNode for genetic algorithm populations.
    Can automatically generate initial populations with configurable parameters.
    """
    
    def __init__(self, name: str = "", data=None, size: int = 10, 
                 genome_length: int = 5, lower_bound: float = -5.12, 
                 upper_bound: float = 5.12, auto_generate: bool = True):
        """
        Initialize a population node for genetic algorithms.
        
        Args:
            name: Name of the node
            data: Initial population data (if provided, overrides auto-generation)
            size: Population size (number of individuals)
            genome_length: Length of each individual's genome/chromosome
            lower_bound: Lower bound for random initialization
            upper_bound: Upper bound for random initialization
            auto_generate: If True and data is None, automatically generate initial population
        """
        # Store GA-specific parameters
        self.genome_length = genome_length
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.auto_generate = auto_generate
        
        # Generate initial population if needed
        if data is None and auto_generate:
            data = self.generate_population(size, genome_length, lower_bound, upper_bound)
        
        # Call parent constructor with generated or provided data
        super().__init__(name, data, size)
    
    @staticmethod
    def generate_population(pop_size: int, genome_length: int, 
                          lower: float = -5.12, upper: float = 5.12):
        """
        Generate a random population for genetic algorithms.
        
        Args:
            pop_size: Number of individuals in the population
            genome_length: Length of each individual's genome
            lower: Lower bound for gene values
            upper: Upper bound for gene values
            
        Returns:
            List of individuals, where each individual is a list of floats
        """
        return [[random.uniform(lower, upper) for _ in range(genome_length)] 
                for _ in range(pop_size)]
    
    def regenerate_population(self):
        """
        Regenerate the population with current parameters.
        Useful for resetting the GA or trying a new random initialization.
        """
        new_population = self.generate_population(
            self.bufferSize, 
            self.genome_length, 
            self.lower_bound, 
            self.upper_bound
        )
        self.buffer = list(new_population)
        self.value = self.buffer[0] if self.buffer else None
        return new_population
    
    def set_bounds(self, lower: float, upper: float):
        """
        Update the bounds for population generation.
        
        Args:
            lower: New lower bound
            upper: New upper bound
        """
        self.lower_bound = lower
        self.upper_bound = upper
    
    def set_genome_length(self, length: int):
        """
        Update the genome length.
        
        Args:
            length: New genome length
        """
        self.genome_length = length
    
    def get_population_stats(self):
        """
        Get statistics about the current population.
        
        Returns:
            Dictionary with population statistics
        """
        if not self.buffer or len(self.buffer) == 0:
            return {
                'size': 0,
                'genome_length': self.genome_length,
                'lower_bound': self.lower_bound,
                'upper_bound': self.upper_bound
            }
        
        # Calculate statistics
        stats = {
            'size': len(self.buffer),
            'genome_length': len(self.buffer[0]) if self.buffer[0] else 0,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound
        }
        
        return stats
