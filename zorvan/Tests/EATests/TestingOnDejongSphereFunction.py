# Backwards-compatible shim to re-export run_graph_ea from Experiments/exp_graph_ea_dejong_sphere.py

import importlib.util
import os

HERE = os.path.dirname(__file__)
TARGET = os.path.join(
    HERE, "..", "..", "..", "Experiments", "exp_graph_ea_dejong_sphere.py"
)
TARGET = os.path.normpath(TARGET)

if os.path.exists(TARGET):
    spec = importlib.util.spec_from_file_location("exp_graph_ea_dejong_sphere", TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    run_graph_ea = getattr(module, "run_graph_ea")
    print(
        "Warning: TestingOnDejongSphereFunction.py has moved to Experiments/exp_graph_ea_dejong_sphere.py"
    )
else:
    raise ImportError("Missing Experiments/exp_graph_ea_dejong_sphere.py")

from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.BulkTournamentNode import BulkTournamentNode
from zorvan.Nodes.DeJongSphereNode import DeJongSphereNode
from zorvan.Nodes.ElitismNode import ElitismNode
from zorvan.Nodes.ExtractListElement import ExtractListElement
from zorvan.Nodes.MutationNode import MutaionNode
from zorvan.Nodes.PopulationNode import PopulationNode
from zorvan.Nodes.SequencerNode import SequencerNode
from zorvan.Nodes.SingleInputCrossover import SingleInputCrossover


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
        num_selections=pop_size
        - num_elites,  # Select fewer to make room for elite individual(s)
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
    # The graph has inherent delays:
    # 1. Network length (longest path through nodes): ~8 nodes
    # 2. Tournament selection delay: outputs (pop_size - num_elites) candidates sequentially
    # 3. Population streaming: pop_size iterations to stream through population node
    #
    # Formula per generation: network_length + pop_size + (pop_size - num_elites)
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

    # Get current best from final generation
    best_fitness = elite_fitnesses[0] if elite_fitnesses else float("inf")
    best_individual = elite_individuals[0] if elite_individuals else None

    # Extract fitness history from elite collector buffer
    # The elite collector has been gathering best individuals from each generation
    # ElitismNode returns a list of elites, so we need to extract the first one
    fitness_history = []
    for elite_list in eliteCollector.buffer:
        if elite_list is not None and isinstance(elite_list, list):
            # elite_list is [elite1, elite2, ...] where each elite is a genome
            # Get the first elite (best one)
            if len(elite_list) > 0 and isinstance(elite_list[0], list):
                elite = elite_list[0]  # First elite from this generation
                # Calculate its fitness
                fitness = sum(gene**2 for gene in elite)
                fitness_history.append(fitness)

    if verbose:
        print(f"Best fitness in final generation: {best_fitness:.6f}")
        print(f"Fitness history length: {len(fitness_history)} generations tracked")
        print(f"Final best fitness: {best_fitness:.6f}")

    return best_individual, best_fitness, fitness_history


# Backwards-compatible shim to re-export run_graph_ea from Experiments/exp_graph_ea_dejong_sphere.py

import importlib.util
import os

HERE = os.path.dirname(__file__)
TARGET = os.path.join(
    HERE, "..", "..", "..", "Experiments", "exp_graph_ea_dejong_sphere.py"
)
TARGET = os.path.normpath(TARGET)

if os.path.exists(TARGET):
    spec = importlib.util.spec_from_file_location("exp_graph_ea_dejong_sphere", TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    run_graph_ea = getattr(module, "run_graph_ea")
    # Deprecation warning for interactive use
    print(
        "Warning: TestingOnDejongSphereFunction.py has moved to Experiments/exp_graph_ea_dejong_sphere.py"
    )
else:
    raise ImportError("Missing Experiments/exp_graph_ea_dejong_sphere.py")

# No __main__ interactive plotting here — run the Experiments script directly for plotting/CLI behavior.
