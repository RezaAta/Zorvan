# Moved from ComputationalGraphs/Tests/EATests/TestingOnDejongSphereFunction.py
# Renamed to Experiments/exp_graph_ea_dejong_sphere.py

"""
Graph-based EA running on DeJong Sphere Function.
"""

import matplotlib.pyplot as plt

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.BulkTournamentNode import BulkTournamentNode
from ComputationalGraphs.Nodes.DeJongSphereNode import DeJongSphereNode
from ComputationalGraphs.Nodes.ElitismNode import ElitismNode
from ComputationalGraphs.Nodes.ExtractListElement import ExtractListElement
from ComputationalGraphs.Nodes.MutationNode import MutaionNode
from ComputationalGraphs.Nodes.PopulationNode import PopulationNode
from ComputationalGraphs.Nodes.SequencerNode import SequencerNode
from ComputationalGraphs.Nodes.SingleInputCrossover import SingleInputCrossover


def run_graph_ea(
    pop_size=50, genome_length=5, generations=100, num_elites=1, verbose=True
):
    """
    Run the computational graph EA using the exact same structure as the GUI example.
    Returns best individual, best fitness, and fitness history tracked per generation.
    """

    # Build the graph - EXACT same structure as GUI example
    graph = Graph()

    # Population node - auto-generates initial population
    populationNode = PopulationNode(
        name="Population",
        size=pop_size,
        genome_length=genome_length,
        lower_bound=-5.12,
        upper_bound=5.12,
        auto_generate=True,
    )

    # Population buffer (size 1 to stream individuals)
    populationBuffer = BufferNode("Pop_Buffer", size=1)
    populationBuffer.AddPreNode(populationNode)

    # Fitness evaluation (De Jong sphere function)
    fitnessNode = DeJongSphereNode("Fitness")
    fitnessNode.AddPreNode(populationNode)

    # ELITISM: Track best N individuals from each generation
    elitismNode = ElitismNode(
        "Elitism", population_size=pop_size, num_elites=num_elites
    )
    elitismNode.AddPreNode(populationBuffer)  # Gets individuals
    elitismNode.AddPreNode(fitnessNode)  # Gets fitness values

    # Collect elite individuals from each generation (filters out None values)
    # Size = number of generations to track
    eliteCollector = BufferNode("Elite_Collector", size=generations, allowNone=False)
    eliteCollector.AddPreNode(elitismNode)

    # Tournament selection (bulk mode) - selects pop_size-num_elites to leave room for elites
    tournamentNode = BulkTournamentNode(
        "Tournament",
        tournamentSize=3,
        populationSize=pop_size,
        num_selections=pop_size - num_elites,
    )
    tournamentNode.AddPreNode(populationBuffer)
    tournamentNode.AddPreNode(fitnessNode)

    # Crossover (match classic EA: rate=0.9)
    crossoverNode = SingleInputCrossover(name="Crossover", delay=0, rate=0.9)
    crossoverNode.AddPreNode(tournamentNode)

    # Extract children
    firstChild = ExtractListElement("Child_0", 0)
    firstChild.AddPreNode(crossoverNode)

    secondChild = ExtractListElement("Child_1", 1)
    secondChild.AddPreNode(crossoverNode)

    # Sequence children together
    crossoverPopulation = SequencerNode("Children", None)
    crossoverPopulation.AddPreNode(firstChild, secondChild)

    # Mutation (match classic EA parameters: rate=0.1, scale=0.1)
    mutationNode = MutaionNode("Mutation", rate=0.1, scale=0.1)
    mutationNode.AddPreNode(crossoverPopulation)

    # Combine mutated offspring with elite individual
    finalPopulation = SequencerNode("Final_Pop", None)
    finalPopulation.AddPreNode(mutationNode)
    finalPopulation.AddPreNode(elitismNode)  # Add best individual

    # Close the loop
    populationNode.AddPreNode(finalPopulation)

    # Add all nodes to graph
    graph.AddNode(
        populationNode,
        populationBuffer,
        fitnessNode,
        elitismNode,
        eliteCollector,
        tournamentNode,
        crossoverNode,
        firstChild,
        secondChild,
        crossoverPopulation,
        mutationNode,
        finalPopulation,
    )

    # Calculate total iterations
    network_length = 8  # Longest path through the graph
    tournament_candidates = pop_size - num_elites
    iterations_per_generation = network_length + pop_size + tournament_candidates
    total_iterations = iterations_per_generation * generations

    if verbose:
        print(
            f"Running Graph EA: {generations} generations x {pop_size} population = {total_iterations} iterations"
        )

    # Run graph
    graphProcessor = GraphProcessor(graph=graph)
    graphProcessor.verbose = False
    graphProcessor.ComputeGraph(total_iterations)

    # Extract results from elitism node
    elite_individuals = elitismNode.elite_individuals
    elite_fitnesses = elitismNode.elite_fitnesses

    best_fitness = elite_fitnesses[0] if elite_fitnesses else float("inf")
    best_individual = elite_individuals[0] if elite_individuals else None

    fitness_history = []
    for elite_list in eliteCollector.buffer:
        if elite_list is not None and isinstance(elite_list, list):
            if len(elite_list) > 0 and isinstance(elite_list[0], list):
                elite = elite_list[0]
                fitness = sum(gene**2 for gene in elite)
                fitness_history.append(fitness)

    if verbose:
        print(f"Best fitness in final generation: {best_fitness:.6f}")
        print(f"Fitness history length: {len(fitness_history)} generations tracked")
        print(f"Final best fitness: {best_fitness:.6f}")

    return best_individual, best_fitness, fitness_history


if __name__ == "__main__":
    pop_size = 50
    genome_length = 5
    generations = 100
    num_elites = 1

    print(
        f"Running Computational Graph EA: DeJong Sphere, {num_elites} elite(s), {generations} gen, {pop_size} pop"
    )
    print("=" * 70)

    best_solution, best_fitness, fitness_history = run_graph_ea(
        pop_size=pop_size,
        genome_length=genome_length,
        generations=generations,
        num_elites=num_elites,
        verbose=True,
    )

    print("=" * 70)
    print(f"Best solution: {best_solution}")
    print(f"Best fitness: {best_fitness:.6f}")

    plt.figure(figsize=(10, 6))
    plt.plot(
        range(1, len(fitness_history) + 1),
        fitness_history,
        "g-",
        linewidth=2,
        label="Best Fitness",
    )
    plt.xlabel("Generation", fontsize=12)
    plt.ylabel("Fitness (Lower is Better)", fontsize=12)
    plt.yscale("log")
    plt.title(
        f"Graph EA - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop\nBest: {best_fitness:.6f}",
        fontsize=12,
    )
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    filename = f"Graph_DeJong_Sphere_{num_elites}Elite_{generations}Gen_{pop_size}Pop_Best{best_fitness:.6f}.png"
    plt.savefig(filename, dpi=150)
    print(f"Plot saved as: {filename}")
    plt.show()
