"""Example graphs loader for the GUI."""

from typing import List, Callable
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
from ComputationalGraphs.Nodes.MinNode import MinNode
from ComputationalGraphs.Nodes.MaxNode import MaxNode
from ComputationalGraphs.Nodes.PiecewiseLinearNode import PiecewiseLinearNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
from ComputationalGraphs.Nodes.DivisionNode import DivisionNode


class ExampleCategory:
    """Represents a category of examples."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.examples: List[tuple] = []
    
    def add_example(self, name: str, description: str, builder: Callable[[], Graph]):
        """Add an example to this category."""
        self.examples.append((name, description, builder))


class ExamplesLoader:
    """Manages and loads example graphs."""
    
    def __init__(self):
        self.categories = {}
        self._register_examples()
    
    def _register_examples(self):
        """Register all available examples."""
        # Basic Examples
        basic = ExampleCategory("Basic", "Simple computational graphs")
        basic.add_example(
            "Fibonacci Sequence",
            "Demonstrates recursive computation using feedback loops",
            self._build_fibonacci
        )
        basic.add_example(
            "Simple Addition Chain",
            "Chain of addition nodes showing sequential computation",
            self._build_addition_chain
        )
        self.categories["basic"] = basic
        
        # Forward Processing Neural Network Examples
        nn_forward = ExampleCategory("Neural Networks - Forward Processing", "MLP with forward processing (no buffers)")
        nn_forward.add_example(
            "XOR Problem (2-2-1)",
            "2-input XOR with 2-neuron hidden layer using sigmoid activation",
            self._build_xor_mlp
        )
        nn_forward.add_example(
            "Simple MLP (1-1-1)",
            "Minimal MLP for understanding the architecture",
            self._build_simple_mlp
        )
        nn_forward.add_example(
            "Iris Classification (4-5-3-3)",
            "Multi-class classification with two hidden layers",
            self._build_iris_mlp
        )
        self.categories["neural_networks_forward"] = nn_forward
        
        # Concurrent Processing Neural Network Examples
        nn_concurrent = ExampleCategory("Neural Networks - Concurrent Processing", "MLP with concurrent processing (with buffers)")
        nn_concurrent.add_example(
            "XOR Problem (2-2-1) - Concurrent",
            "2-input XOR with buffers for concurrent execution",
            self._build_xor_mlp_concurrent
        )
        nn_concurrent.add_example(
            "Simple MLP (1-1-1) - Concurrent",
            "Minimal MLP with buffer synchronization",
            self._build_simple_mlp_concurrent
        )
        self.categories["neural_networks_concurrent"] = nn_concurrent
        
        # Fuzzy System Examples
        fuzzy = ExampleCategory("Fuzzy Systems", "Fuzzy logic control systems")
        fuzzy.add_example(
            "Temperature Control (Fan Speed)",
            "Fan speed control based on temperature and humidity using Mamdani fuzzy rules",
            self._build_temperature_control
        )
        self.categories["fuzzy_systems"] = fuzzy
        
        # Evolutionary Algorithm Examples
        ea = ExampleCategory("Evolutionary Algorithms", "Optimization using evolutionary computation")
        ea.add_example(
            "De Jong Sphere Function",
            "Minimizing the sphere function using tournament selection and genetic operators",
            self._build_dejong_ea
        )
        ea.add_example(
            "De Jong with Elitism",
            "GA with elitism - best individual preserved across generations",
            self._build_dejong_ea_elitism
        )
        self.categories["evolutionary_algorithms"] = ea
    
    def get_categories(self) -> List[ExampleCategory]:
        """Get all example categories."""
        return list(self.categories.values())
    
    def _build_fibonacci(self) -> Graph:
        """Build Fibonacci sequence graph."""
        graph = Graph()
        fib1 = DisplayNode(name="Fibonacci_n-1", value=1)
        fibn = AdditionNode(name="Fibonacci_n", value=1)
        
        graph.AddNode(fib1, fibn)
        graph.ConnectPreNode(fibn, fibn, fib1)
        graph.ConnectPreNode(fib1, fibn)
        graph.UpdateAdjacencyMatrix()
        
        return graph
    
    def _build_addition_chain(self) -> Graph:
        """Build simple addition chain."""
        graph = Graph()
        
        a = DisplayNode(name="A", value=1)
        b = DisplayNode(name="B", value=2)
        c = DisplayNode(name="C", value=3)
        
        sum1 = AdditionNode(name="A+B", value=0)
        sum1.AddPreNode(a, b)
        
        sum2 = AdditionNode(name="(A+B)+C", value=0)
        sum2.AddPreNode(sum1, c)
        
        graph.AddNode(a, b, c, sum1, sum2)
        graph.UpdateAdjacencyMatrix()
        
        return graph
    
    def _build_xor_mlp(self) -> Graph:
        """Build XOR MLP with backpropagation (Forward Processing version)."""
        from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from ComputationalGraphs.Core.BackpropGraphForwardProcessing import BackpropGraphForwardProcessing
        from ComputationalGraphs.Nodes.LinearNode import LinearNode
        
        # Create MLP without buffers (for forward processing)
        mlpGraph = MLPGraphForwardProcessing(
            numInputs=2,
            numOutputs=1,
            numHiddenLayers=1,
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode  # Linear output for regression
        )
        mlpGraph.BuildMLP()
        
        # Load complete XOR dataset (all 4 samples)
        X_train = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
        y_train = [[0.0], [1.0], [1.0], [0.0]]
        mlpGraph.LoadData(X_train, y_train)
        
        # Add backpropagation (no buffers)
        backprop_graph = BackpropGraphForwardProcessing(mlpGraph, learningRate=0.5)
        backprop_graph.BuildBackprop()
        
        # Combine graphs
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        
        # Set starting nodes for forward processing (ONLY the first layer multiplication nodes)
        # Weight nodes will be marked as 'processed' by the GUI's graph_runner automatically
        # Make a copy to avoid reference issues
        fullGraph.starting_nodes = list(mlpGraph.starting_nodes)
        # Copy stopping nodes (weights) from the MLP so the GUI/processor can respect them
        if hasattr(mlpGraph, 'stopping_nodes'):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)
        fullGraph.UpdateAdjacencyMatrix()
        
        return fullGraph
    
    def _build_simple_mlp(self) -> Graph:
        """Build minimal 1x1x1 MLP - Forward Processing version."""
        from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from ComputationalGraphs.Nodes.LinearNode import LinearNode
        
        mlpGraph = MLPGraphForwardProcessing(
            numInputs=1,
            numOutputs=1,
            numHiddenLayers=1,
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode
        )
        mlpGraph.BuildMLP()
        
        # Load sample data (simple linear relationship)
        X_train = [[0.0], [0.25], [0.5], [0.75], [1.0]]
        y_train = [[0.0], [0.25], [0.5], [0.75], [1.0]]
        mlpGraph.LoadData(X_train, y_train)
        
        mlpGraph.UpdateAdjacencyMatrix()
        
        return mlpGraph
    
    def _build_iris_mlp(self) -> Graph:
        """Build Iris classification MLP (4-5-3-3) - Forward Processing version."""
        from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from ComputationalGraphs.Core.BackpropGraphForwardProcessing import BackpropGraphForwardProcessing
        from ComputationalGraphs.Nodes.LinearNode import LinearNode
        
        mlpGraph = MLPGraphForwardProcessing(
            numInputs=4,
            numOutputs=3,
            numHiddenLayers=2,
            hiddenLayerSizes=[5, 3],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode
        )
        mlpGraph.BuildMLP()
        
        # Load sample Iris data (3 samples, one from each class)
        X_train = [
            [5.1, 3.5, 1.4, 0.2],  # Setosa
            [7.0, 3.2, 4.7, 1.4],  # Versicolor
            [6.3, 3.3, 6.0, 2.5]   # Virginica
        ]
        y_train = [
            [1.0, 0.0, 0.0],  # Setosa
            [0.0, 1.0, 0.0],  # Versicolor
            [0.0, 0.0, 1.0]   # Virginica
        ]
        mlpGraph.LoadData(X_train, y_train)
        
        backprop_graph = BackpropGraphForwardProcessing(mlpGraph, learningRate=0.01)
        backprop_graph.BuildBackprop()
        
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        
        # Set starting nodes (ONLY the first layer multiplication nodes)
        # Make a copy to avoid reference issues
        fullGraph.starting_nodes = list(mlpGraph.starting_nodes)
        # Copy stopping nodes (weights) from the MLP so the GUI/processor can respect them
        if hasattr(mlpGraph, 'stopping_nodes'):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)
        
        fullGraph.UpdateAdjacencyMatrix()
        
        return fullGraph
    
    def _build_temperature_control(self) -> Graph:
        """Build temperature control fuzzy system."""
        graph = Graph()
        
        # Inputs
        humidity = DisplayNode("Humidity", value=80)
        temperature = DisplayNode("Temperature", value=44)
        graph.AddNode(temperature, humidity)
        
        # Temperature membership functions
        hot = PiecewiseLinearNode("Hot", xs=[-20, 5, 25, 45, 100], mus=[0.0, 0.0, 0.5, 1.0, 1.0])
        hot.AddPreNode(temperature)
        cold = PiecewiseLinearNode("Cold", xs=[-20, 5, 25, 45, 100], mus=[1.0, 1.0, 0.5, 0.0, 0.0])
        cold.AddPreNode(temperature)
        
        # Humidity membership functions
        high_hum = PiecewiseLinearNode("High_Humidity", xs=[0, 25, 50, 75, 100], mus=[0.0, 0.0, 0.5, 1.0, 1.0])
        high_hum.AddPreNode(humidity)
        low_hum = PiecewiseLinearNode("Low_Humidity", xs=[0, 25, 50, 75, 100], mus=[1.0, 1.0, 0.5, 0.0, 0.0])
        low_hum.AddPreNode(humidity)
        
        graph.AddNode(hot, cold, high_hum, low_hum)
        
        # Rules (MIN for AND)
        hot_high = MinNode("Hot_AND_High")
        hot_high.AddPreNode(hot, high_hum)
        
        hot_low = MinNode("Hot_AND_Low")
        hot_low.AddPreNode(hot, low_hum)
        
        cold_high = MinNode("Cold_AND_High")
        cold_high.AddPreNode(cold, high_hum)
        
        cold_low = MinNode("Cold_AND_Low")
        cold_low.AddPreNode(cold, low_hum)
        
        graph.AddNode(hot_high, hot_low, cold_high, cold_low)
        
        # Aggregate (MAX for OR)
        moderate_rule = MaxNode("Moderate_Rule")
        moderate_rule.AddPreNode(hot_low, cold_high)
        graph.AddNode(moderate_rule)
        
        # Output speeds
        high_speed = DisplayNode("High_Speed", 100)
        mod_speed = DisplayNode("Moderate_Speed", 50)
        low_speed = DisplayNode("Low_Speed", 25)
        graph.AddNode(high_speed, mod_speed, low_speed)
        
        # Weighted outputs
        aH = MultiplicationNode("aH")
        aH.AddPreNode(hot_high, high_speed)
        aM = MultiplicationNode("aM")
        aM.AddPreNode(moderate_rule, mod_speed)
        aL = MultiplicationNode("aL")
        aL.AddPreNode(cold_low, low_speed)
        graph.AddNode(aH, aM, aL)
        
        # Defuzzification
        numerator = AdditionNode("Numerator")
        numerator.AddPreNode(aH, aM, aL)
        denominator = AdditionNode("Denominator")
        denominator.AddPreNode(hot_high, moderate_rule, cold_low)
        fanspeed = DivisionNode("Fan_Speed")
        fanspeed.AddPreNode(numerator, denominator)
        graph.AddNode(numerator, denominator, fanspeed)
        
        graph.UpdateAdjacencyMatrix()
        return graph
    
    def _build_xor_mlp_concurrent(self) -> Graph:
        """Build XOR MLP with backpropagation (Concurrent Processing with buffers).
        Configuration matches TestingOnXOR.py exactly.
        
        NOTE: Error buffers are NOT added to the graph in this builder.
        They should be created after warmup phase, just like in TestingOnXOR.py.
        For GUI usage, error buffers should be added separately if needed for tracking.
        """
        from ComputationalGraphs.Core.MLPGraph import MLPGraph
        from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
        from ComputationalGraphs.Nodes.LinearNode import LinearNode
        
        # Create MLP with buffers (for concurrent processing)
        # EXACT CONFIG: numInputs=2, numOutputs=1, numHiddenLayers=1 (default size=2)
        # activationFunction=SigmoidNode, outputLayerType=LinearNode
        mlpGraph = MLPGraph(
            numInputs=2,
            numOutputs=1,
            numHiddenLayers=1,
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode  # Linear output for regression
        )
        mlpGraph.BuildMLP()
        
        # EXACT CONFIG: Learning rate = 0.01 (not 0.5!)
        backprop_graph = BackpropGraph(mlpGraph, learningRate=0.01)
        backprop_graph.BuildBackprop()
        
        # EXACT CONFIG: XOR Dataset - Row-per-feature format
        X = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]
        y = [[0.0, 1.0, 1.0, 0.0]]
        mlpGraph.LoadData(X, y)
        
        # Combine graphs (WITHOUT error buffers - they're added after warmup in TestingOnXOR.py)
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        
        # Set starting nodes for concurrent processing (data stream nodes + labels)
        fullGraph.starting_nodes = [input[0] for input in mlpGraph.inputLayer] + mlpGraph.labelLayer
        fullGraph.UpdateAdjacencyMatrix()
        
        # Store reference to mlpGraph for potential error buffer creation later
        fullGraph._mlp_graph = mlpGraph
        
        return fullGraph
    
    def _build_simple_mlp_concurrent(self) -> Graph:
        """Build minimal 1x1x1 MLP - Concurrent Processing with buffers."""
        from ComputationalGraphs.Core.MLPGraph import MLPGraph
        from ComputationalGraphs.Nodes.LinearNode import LinearNode
        
        mlpGraph = MLPGraph(
            numInputs=1,
            numOutputs=1,
            numHiddenLayers=1,
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode
        )
        mlpGraph.BuildMLP()
        
        # Load sample data (simple linear relationship) - Row-per-feature format
        X_train = [[0.0, 0.25, 0.5, 0.75, 1.0]]
        y_train = [[0.0, 0.25, 0.5, 0.75, 1.0]]
        mlpGraph.LoadData(X_train, y_train)
        
        mlpGraph.UpdateAdjacencyMatrix()
        
        return mlpGraph
    
    def _build_dejong_ea(self) -> Graph:
        """Build De Jong sphere function EA example - complete GA loop with tournament selection."""
        from ComputationalGraphs.Nodes.PopulationNode import PopulationNode
        from ComputationalGraphs.Nodes.BufferNode import BufferNode
        from ComputationalGraphs.Nodes.DeJongSphereNode import DeJongSphereNode
        from ComputationalGraphs.Nodes.BulkTournamentNode import BulkTournamentNode
        from ComputationalGraphs.Nodes.SingleInputCrossover import SingleInputCrossover
        from ComputationalGraphs.Nodes.ExtractListElement import ExtractListElement
        from ComputationalGraphs.Nodes.SequencerNode import SequencerNode
        from ComputationalGraphs.Nodes.MutationNode import MutaionNode
        
        graph = Graph()
        
        # GA parameters
        pop_size = 10
        genome_length = 5
        
        # Population node - auto-generates initial population!
        populationNode = PopulationNode(
            name="Population", 
            size=pop_size,
            genome_length=genome_length,
            lower_bound=-5.12,
            upper_bound=5.12,
            auto_generate=True
        )
        
        # Population buffer (size 1 to stream individuals)
        populationBuffer = BufferNode("Pop_Buffer", size=1)
        populationBuffer.AddPreNode(populationNode)
        
        # Fitness evaluation (De Jong sphere function)
        fitnessNode = DeJongSphereNode("Fitness")
        fitnessNode.AddPreNode(populationNode)
        
        # Tournament selection (bulk mode - collects entire population then selects)
        tournamentNode = BulkTournamentNode("Tournament", tournamentSize=3, populationSize=pop_size)
        tournamentNode.AddPreNode(populationBuffer)
        tournamentNode.AddPreNode(fitnessNode)
        
        # Crossover (single input - collects pairs and produces offspring)
        crossoverNode = SingleInputCrossover(name="Crossover", delay=0)
        crossoverNode.AddPreNode(tournamentNode)
        
        # Extract children from crossover output
        firstChild = ExtractListElement("Child_0", 0)
        firstChild.AddPreNode(crossoverNode)
        
        secondChild = ExtractListElement("Child_1", 1)
        secondChild.AddPreNode(crossoverNode)
        
        # Sequence children together
        crossoverPopulation = SequencerNode("Children", None)
        crossoverPopulation.AddPreNode(firstChild, secondChild)
        
        # Mutation
        mutationNode = MutaionNode("Mutation")
        mutationNode.AddPreNode(crossoverPopulation)
        
        # Close the loop: mutation feeds back to population
        populationNode.AddPreNode(mutationNode)
        
        # Add all nodes to graph
        graph.AddNode(populationNode, populationBuffer, fitnessNode, tournamentNode,
                      crossoverNode, firstChild, secondChild, crossoverPopulation, mutationNode)
        
        graph.UpdateAdjacencyMatrix()
        return graph
    
    def _build_dejong_ea_elitism(self) -> Graph:
        """Build De Jong EA with elitism - best individual preserved across generations."""
        from ComputationalGraphs.Nodes.PopulationNode import PopulationNode
        from ComputationalGraphs.Nodes.BufferNode import BufferNode
        from ComputationalGraphs.Nodes.DeJongSphereNode import DeJongSphereNode
        from ComputationalGraphs.Nodes.BulkTournamentNode import BulkTournamentNode
        from ComputationalGraphs.Nodes.SingleInputCrossover import SingleInputCrossover
        from ComputationalGraphs.Nodes.ExtractListElement import ExtractListElement
        from ComputationalGraphs.Nodes.SequencerNode import SequencerNode
        from ComputationalGraphs.Nodes.MutationNode import MutaionNode
        from ComputationalGraphs.Nodes.ElitismNode import ElitismNode
        
        graph = Graph()
        
        # GA parameters
        pop_size = 10
        genome_length = 5
        
        # Population node - auto-generates initial population with elitism support!
        populationNode = PopulationNode(
            name="Population",
            size=pop_size,
            genome_length=genome_length,
            lower_bound=-5.12,
            upper_bound=5.12,
            auto_generate=True
        )
        
        # Population buffer (size 1 to stream individuals)
        populationBuffer = BufferNode("Pop_Buffer", size=1)
        populationBuffer.AddPreNode(populationNode)
        
        # Fitness evaluation (De Jong sphere function)
        fitnessNode = DeJongSphereNode("Fitness")
        fitnessNode.AddPreNode(populationNode)
        
        # ELITISM: Track best N individuals from each generation
        num_elites = 1  # Keep top 1 individual(s) - adjustable parameter
        elitismNode = ElitismNode("Elitism", population_size=pop_size, num_elites=num_elites)
        elitismNode.AddPreNode(populationBuffer)  # Gets individuals
        elitismNode.AddPreNode(fitnessNode)       # Gets fitness values
        
        # Collect elite individuals from each generation (filters out None values)
        # Size = number of generations you want to run (e.g., 100 generations)
        # allowNone=False means None values will be discarded
        eliteCollector = BufferNode("Elite_Collector", size=100, allowNone=False)
        eliteCollector.AddPreNode(elitismNode)
        
        # Tournament selection (bulk mode) - selects pop_size-num_elites to leave room for elites
        tournamentNode = BulkTournamentNode(
            "Tournament", 
            tournamentSize=3, 
            populationSize=pop_size,
            num_selections=pop_size-num_elites  # Select fewer to make room for elite individual(s)
        )
        tournamentNode.AddPreNode(populationBuffer)
        tournamentNode.AddPreNode(fitnessNode)
        
        # Crossover
        crossoverNode = SingleInputCrossover(name="Crossover", delay=0)
        crossoverNode.AddPreNode(tournamentNode)
        
        # Extract children
        firstChild = ExtractListElement("Child_0", 0)
        firstChild.AddPreNode(crossoverNode)
        
        secondChild = ExtractListElement("Child_1", 1)
        secondChild.AddPreNode(crossoverNode)
        
        # Sequence children together
        crossoverPopulation = SequencerNode("Children", None)
        crossoverPopulation.AddPreNode(firstChild, secondChild)
        
        # Mutation
        mutationNode = MutaionNode("Mutation")
        mutationNode.AddPreNode(crossoverPopulation)
        
        # Combine mutated offspring with elite individual
        # The elite will be inserted into the population along with offspring
        finalPopulation = SequencerNode("Final_Pop", None)
        finalPopulation.AddPreNode(mutationNode)
        finalPopulation.AddPreNode(elitismNode)  # Add best individual
        
        # Close the loop
        populationNode.AddPreNode(finalPopulation)
        
        # Add all nodes to graph
        graph.AddNode(populationNode, populationBuffer, fitnessNode, elitismNode,
                      eliteCollector, tournamentNode, crossoverNode, firstChild, secondChild, 
                      crossoverPopulation, mutationNode, finalPopulation)
        
        graph.UpdateAdjacencyMatrix()
        return graph
