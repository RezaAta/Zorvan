"""Example graphs loader for the GUI."""

from typing import Callable, List

from zorvan.Core.Graph import Graph
from zorvan.Nodes.AdditionNode import AdditionNode
from zorvan.Nodes.DisplayNode import DisplayNode
from zorvan.Nodes.SigmoidNode import SigmoidNode


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
            self._build_fibonacci,
        )
        basic.add_example(
            "Simple Addition Chain",
            "Chain of addition nodes showing sequential computation",
            self._build_addition_chain,
        )
        basic.add_example(
            "Fully Connected Addition (3 nodes)",
            "3 addition nodes fully connected - values double each iteration (start=1)",
            self._build_fully_connected_addition,
        )
        self.categories["basic"] = basic

        # Concurrent Processing Neural Network Examples (with buffers)
        nn_concurrent = ExampleCategory(
            "Neural Networks - Concurrent",
            "MLP with concurrent processing (all nodes compute each iteration, uses buffers)",
        )
        nn_concurrent.add_example(
            "XOR Problem (2-2-1) - Concurrent",
            "2-input XOR with buffers for concurrent execution",
            self._build_xor_mlp_concurrent,
        )
        nn_concurrent.add_example(
            "Simple MLP (1-1-1) - Concurrent",
            "Minimal MLP with buffer synchronization",
            self._build_simple_mlp_concurrent,
        )
        nn_concurrent.add_example(
            "Iris Classification (4-5-3-3)",
            "Multi-class classification with two hidden layers",
            self._build_iris_mlp_concurrent,
        )
        self.categories["neural_networks_concurrent"] = nn_concurrent

        # Forward Processing Neural Network Examples (sequence-based, no buffers)
        nn_forward = ExampleCategory(
            "Neural Networks - Forward",
            "MLP with forward processing (nodes execute in dependency order, no buffers)",
        )
        nn_forward.add_example(
            "XOR Problem (2-2-1) - Forward",
            "2-input XOR with forward processing (no buffers)",
            self._build_xor_mlp_forward,
        )
        nn_forward.add_example(
            "Simple MLP (1-1-1) - Forward",
            "Minimal MLP with forward processing (no buffers)",
            self._build_simple_mlp_forward,
        )
        nn_forward.add_example(
            "XOR Problem (2-2-1) - Forward (Bias)",
            "XOR forward-processing MLP with explicit bias nodes enabled",
            self._build_xor_mlp_forward_bias,
        )
        self.categories["neural_networks_forward"] = nn_forward

        # Manual Processing Neural Network Examples
        nn_manual = ExampleCategory(
            "Neural Networks - Manual",
            "MLP with user-defined manual execution sequence",
        )
        nn_manual.add_example(
            "XOR Problem (2-2-1) - Manual",
            "2-input XOR with a predefined manual processing sequence",
            self._build_xor_mlp_manual,
        )
        self.categories["neural_networks_manual"] = nn_manual

        # Fuzzy System Examples
        fuzzy = ExampleCategory("Fuzzy Systems", "Fuzzy logic control systems")
        # ANFIS (fusion hybrid) example - added for GUI exploration
        fuzzy.add_example(
            "ANFIS XOR (Concurrent GUI)",
            "Zero-order Sugeno ANFIS trained with concurrent backprop - XOR dataset",
            self._build_anfis_xor,
        )
        self.categories["fuzzy_systems"] = fuzzy

        # Evolutionary Algorithm Examples
        ea = ExampleCategory(
            "Evolutionary Algorithms", "Optimization using evolutionary computation"
        )
        ea.add_example(
            "De Jong Sphere Function",
            "Minimizing the sphere function using tournament selection and genetic operators",
            self._build_dejong_ea,
        )
        ea.add_example(
            "De Jong with Elitism",
            "GA with elitism - best individual preserved across generations",
            self._build_dejong_ea_elitism,
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

    def _build_fully_connected_addition(self) -> Graph:
        """Build 3 fully connected addition nodes.

        Each node has the other 2 as predecessors.
        All start with value=1, so after each iteration values double:
        - Iteration 0: A=1, B=1, C=1
        - Iteration 1: A=2, B=2, C=2  (each computes 1+1)
        - Iteration 2: A=4, B=4, C=4  (each computes 2+2)
        - Iteration 3: A=8, B=8, C=8  (each computes 4+4)
        """
        graph = Graph()

        # Create 3 addition nodes, all initialized to 1
        a = AdditionNode(name="A", value=1)
        b = AdditionNode(name="B", value=1)
        c = AdditionNode(name="C", value=1)

        # Fully connect: each node has the other 2 as predecessors
        a.AddPreNode(b, c)  # A computes B + C
        b.AddPreNode(a, c)  # B computes A + C
        c.AddPreNode(a, b)  # C computes A + B

        # Set GUI positions for nice layout (triangle)
        a.gui_pos = (200, 100)
        b.gui_pos = (100, 250)
        c.gui_pos = (300, 250)

        graph.AddNode(a, b, c)
        graph.UpdateAdjacencyMatrix()

        return graph

    def _build_xor_mlp(self) -> Graph:
        """Build XOR MLP with backpropagation (Forward Processing version)."""
        from zorvan.Core.BackpropGraphForwardProcessing import (
            BackpropGraphForwardProcessing,
        )
        from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from zorvan.Nodes.LinearNode import LinearNode

        # Create MLP without buffers (for forward processing)
        mlpGraph = MLPGraphForwardProcessing(
            numInputs=2,
            numOutputs=1,
            numHiddenLayers=1,
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,  # Linear output for regression
        )
        mlpGraph.BuildMLP()

        # Load complete XOR dataset (all 4 samples)
        X_train = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
        y_train = [[0.0], [1.0], [1.0], [0.0]]
        mlpGraph.LoadData(X_train, y_train)

        # Add backpropagation (no buffers)
        backprop_graph = BackpropGraphForwardProcessing(mlpGraph, learningRate=0.5)
        backprop_graph.BuildBackprop()

        # Create error buffers and MSE nodes for plotting
        mlpGraph.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X_train))

        # Combine graphs
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        # Add error buffers and MSE nodes to the full graph
        for eb in mlpGraph.errorBuffers:
            if eb not in fullGraph.nodes:
                fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
            if mse not in fullGraph.nodes:
                fullGraph.AddNode(mse)

        # Set starting nodes for forward processing (ONLY the first layer multiplication nodes)
        # Weight nodes will be marked as 'processed' by the GUI's graph_runner automatically
        # Make a copy to avoid reference issues
        fullGraph.starting_nodes = list(mlpGraph.starting_nodes)
        # Copy stopping nodes (weights) from the MLP so the GUI/processor can respect them
        if hasattr(mlpGraph, "stopping_nodes"):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)
        fullGraph.UpdateAdjacencyMatrix()

        return fullGraph

    def _build_simple_mlp(self) -> Graph:
        """Build minimal 1x1x1 MLP - Forward Processing version."""
        from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from zorvan.Nodes.LinearNode import LinearNode

        mlpGraph = MLPGraphForwardProcessing(
            numInputs=1,
            numOutputs=1,
            numHiddenLayers=1,
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # Load sample data (simple linear relationship)
        X_train = [[0.0], [0.25], [0.5], [0.75], [1.0]]
        y_train = [[0.0], [0.25], [0.5], [0.75], [1.0]]
        mlpGraph.LoadData(X_train, y_train)

        # Create error buffers and MSE nodes for plotting
        mlpGraph.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X_train))

        mlpGraph.UpdateAdjacencyMatrix()

        return mlpGraph

    def _build_iris_mlp(self) -> Graph:
        """Build Iris classification MLP (4-5-3-3) - Forward Processing version."""
        from zorvan.Core.BackpropGraphForwardProcessing import (
            BackpropGraphForwardProcessing,
        )
        from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from zorvan.Nodes.LinearNode import LinearNode

        mlpGraph = MLPGraphForwardProcessing(
            numInputs=4,
            numOutputs=3,
            numHiddenLayers=2,
            hiddenLayerSizes=[5, 3],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # Load sample Iris data (3 samples, one from each class)
        X_train = [
            [5.1, 3.5, 1.4, 0.2],  # Setosa
            [7.0, 3.2, 4.7, 1.4],  # Versicolor
            [6.3, 3.3, 6.0, 2.5],  # Virginica
        ]
        y_train = [
            [1.0, 0.0, 0.0],  # Setosa
            [0.0, 1.0, 0.0],  # Versicolor
            [0.0, 0.0, 1.0],  # Virginica
        ]
        mlpGraph.LoadData(X_train, y_train)

        backprop_graph = BackpropGraphForwardProcessing(mlpGraph, learningRate=0.01)
        backprop_graph.BuildBackprop()

        # Create error buffers and MSE nodes for plotting
        mlpGraph.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X_train))

        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        # Add error buffers and MSE nodes to the full graph
        for eb in mlpGraph.errorBuffers:
            if eb not in fullGraph.nodes:
                fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
            if mse not in fullGraph.nodes:
                fullGraph.AddNode(mse)

        # Set starting nodes (ONLY the first layer multiplication nodes)
        # Make a copy to avoid reference issues
        fullGraph.starting_nodes = list(mlpGraph.starting_nodes)
        # Copy stopping nodes (weights) from the MLP so the GUI/processor can respect them
        if hasattr(mlpGraph, "stopping_nodes"):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)

        fullGraph.UpdateAdjacencyMatrix()

        return fullGraph

    def _build_iris_mlp_concurrent(self) -> Graph:
        """Build Iris classification MLP (4-5-3-3) - Concurrent MLP version."""
        import numpy as np

        from zorvan.Core.BackpropGraph import BackpropGraph
        from zorvan.Core.MLPGraph import MLPGraph
        from zorvan.Nodes.LinearNode import LinearNode

        # Build concurrent MLPGraph (matching forward processing architecture)
        mlpGraph = MLPGraph(
            numInputs=4,
            numOutputs=3,
            numHiddenLayers=2,
            hiddenLayerSizes=[5, 3],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # Sample Iris data
        X_train = [
            [5.1, 3.5, 1.4, 0.2],  # Setosa
            [7.0, 3.2, 4.7, 1.4],  # Versicolor
            [6.3, 3.3, 6.0, 2.5],  # Virginica
        ]
        y_train = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

        # Convert to row-per-feature shape expected by concurrent MLP: (features, samples)
        X = np.array(X_train).T.tolist()
        y = np.array(y_train).T.tolist()
        mlpGraph.LoadData(X, y)

        backprop_graph = BackpropGraph(mlpGraph, learningRate=0.01)
        backprop_graph.BuildBackprop()

        # Create error buffers and MSE nodes for plotting
        mlpGraph.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X_train))

        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        # Add error buffers and MSE nodes to the full graph
        for eb in mlpGraph.errorBuffers:
            if eb not in fullGraph.nodes:
                fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
            if mse not in fullGraph.nodes:
                fullGraph.AddNode(mse)

        # Set starting nodes for concurrent processing: data streams + labels
        fullGraph.starting_nodes = [
            input_pair[0] for input_pair in mlpGraph.inputLayer
        ] + mlpGraph.labelLayer
        fullGraph.UpdateAdjacencyMatrix()

        return fullGraph

    def _build_xor_mlp_concurrent(self) -> Graph:
        """Build XOR MLP with backpropagation (Concurrent Processing with buffers).
        Configuration matches TestingOnXOR.py exactly.

        NOTE: Error buffers are NOT added to the graph in this builder.
        They should be created after warmup phase, just like in TestingOnXOR.py.
        For GUI usage, error buffers should be added separately if needed for tracking.
        """
        from zorvan.Core.BackpropGraph import BackpropGraph
        from zorvan.Core.MLPGraph import MLPGraph
        from zorvan.Nodes.LinearNode import LinearNode

        # Create MLP with buffers (for concurrent processing)
        # EXACT CONFIG: numInputs=2, numOutputs=1, numHiddenLayers=1 (default size=2)
        # activationFunction=SigmoidNode, outputLayerType=LinearNode
        mlpGraph = MLPGraph(
            numInputs=2,
            numOutputs=1,
            numHiddenLayers=1,
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,  # Linear output for regression
        )
        mlpGraph.BuildMLP()

        # EXACT CONFIG: Learning rate = 0.01 (not 0.5!)
        backprop_graph = BackpropGraph(mlpGraph, learningRate=0.01)
        backprop_graph.BuildBackprop()

        # EXACT CONFIG: XOR Dataset - Row-per-feature format
        X = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]
        y = [[0.0, 1.0, 1.0, 0.0]]
        mlpGraph.LoadData(X, y)

        # Create error buffers and MSE nodes for plotting
        mlpGraph.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X[0]))

        # Combine graphs (with error buffers and MSE nodes)
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        # Add error buffers and MSE nodes to the full graph
        for eb in mlpGraph.errorBuffers:
            if eb not in fullGraph.nodes:
                fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
            if mse not in fullGraph.nodes:
                fullGraph.AddNode(mse)

        # Set starting nodes for concurrent processing (data stream nodes + labels)
        fullGraph.starting_nodes = [
            input[0] for input in mlpGraph.inputLayer
        ] + mlpGraph.labelLayer
        fullGraph.UpdateAdjacencyMatrix()

        # Store reference to mlpGraph for potential error buffer creation later
        fullGraph._mlp_graph = mlpGraph

        return fullGraph

    def _build_xor_mlp_manual(self) -> Graph:
        """Build XOR MLP wired for ManualProcessing with a predefined sequence.

        This constructs a forward-processing MLP with backprop, combines both
        graphs into a single `Graph` and uses the sequence finder algorithm
        to compute the `manual_processing_sequence` automatically.
        """
        from zorvan.Core.BackpropGraphForwardProcessing import (
            BackpropGraphForwardProcessing,
        )
        from zorvan.Core.GraphProcessor import GraphProcessor
        from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from zorvan.Nodes.LinearNode import LinearNode

        # Build MLP (forward-processing style)
        mlpGraph = MLPGraphForwardProcessing(
            numInputs=2,
            numOutputs=1,
            numHiddenLayers=1,
            hiddenLayerSizes=[2],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # Load XOR dataset (row-per-sample format expected by forward processing)
        X_train = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
        y_train = [[0.0], [1.0], [1.0], [0.0]]
        mlpGraph.LoadData(X_train, y_train)

        # Attach backprop (forward-processing variant)
        backprop_graph = BackpropGraphForwardProcessing(mlpGraph, learningRate=0.5)
        backprop_graph.BuildBackprop()

        # Combine graphs into a single Graph for GUI
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)

        # Set starting nodes for the sequence finder
        fullGraph.starting_nodes = list(mlpGraph.starting_nodes)

        # Set stopping nodes (weight nodes shouldn't trigger successor activation)
        if hasattr(mlpGraph, "stopping_nodes"):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)
        else:
            fullGraph.stopping_nodes = []

        fullGraph.UpdateAdjacencyMatrix()

        # Compute sequence automatically from topology.
        # GraphProcessor.find_execution_sequence applies deterministic
        # intra-step ordering so this aligns with the manual XOR walkthrough.
        processor = GraphProcessor(fullGraph, verbose=False)
        processor.mark_source_nodes_as_processed()
        processor.mark_container_nodes_as_processed()
        seq_result = processor.find_execution_sequence(
            starting_nodes=fullGraph.starting_nodes,
            stopping_nodes=fullGraph.stopping_nodes,
            include_remaining_source_nodes=True,
        )
        sequence = seq_result.get("sequence", [])

        # Remove starting nodes from the manual sequence to avoid duplicate execution
        starting_set = set(getattr(fullGraph, "starting_nodes", []))
        if starting_set:
            filtered_sequence = []
            for step in sequence:
                filtered = [n for n in step if n not in starting_set]
                if filtered:
                    filtered_sequence.append(filtered)
            sequence = filtered_sequence

        # Assign manual sequence and pass length
        if sequence:
            fullGraph.set_manual_processing_sequence(sequence, strict=True)
            fullGraph.manual_pass_length = len(sequence)

        # Store references for debugging/UI
        fullGraph._mlp_graph = mlpGraph
        fullGraph._backprop_graph = backprop_graph

        return fullGraph

    def _build_simple_mlp_concurrent(self) -> Graph:
        """Build minimal 1x1x1 MLP - Concurrent Processing with buffers."""
        from zorvan.Core.MLPGraph import MLPGraph
        from zorvan.Nodes.LinearNode import LinearNode

        mlpGraph = MLPGraph(
            numInputs=1,
            numOutputs=1,
            numHiddenLayers=1,
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # Load sample data (simple linear relationship) - Row-per-feature format
        X_train = [[0.0, 0.25, 0.5, 0.75, 1.0]]
        y_train = [[0.0, 0.25, 0.5, 0.75, 1.0]]
        mlpGraph.LoadData(X_train, y_train)

        # Create error buffers and MSE nodes for plotting
        mlpGraph.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X_train[0]))

        mlpGraph.UpdateAdjacencyMatrix()

        return mlpGraph

    def _build_dejong_ea(self) -> Graph:
        """Build De Jong sphere function EA example - complete GA loop with tournament selection."""
        from zorvan.Nodes.BufferNode import BufferNode
        from zorvan.Nodes.BulkTournamentNode import BulkTournamentNode
        from zorvan.Nodes.DeJongSphereNode import DeJongSphereNode
        from zorvan.Nodes.ExtractListElement import ExtractListElement
        from zorvan.Nodes.MutationNode import MutaionNode
        from zorvan.Nodes.PopulationNode import PopulationNode
        from zorvan.Nodes.SequencerNode import SequencerNode
        from zorvan.Nodes.SingleInputCrossover import SingleInputCrossover

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
            auto_generate=True,
        )

        # Population buffer (size 1 to stream individuals)
        populationBuffer = BufferNode("Pop_Buffer", size=1)
        populationBuffer.AddPreNode(populationNode)

        # Fitness evaluation (De Jong sphere function)
        fitnessNode = DeJongSphereNode("Fitness")
        fitnessNode.AddPreNode(populationNode)

        # Tournament selection (bulk mode - collects entire population then selects)
        tournamentNode = BulkTournamentNode(
            "Tournament", tournamentSize=3, populationSize=pop_size
        )
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
        graph.AddNode(
            populationNode,
            populationBuffer,
            fitnessNode,
            tournamentNode,
            crossoverNode,
            firstChild,
            secondChild,
            crossoverPopulation,
            mutationNode,
        )

        graph.UpdateAdjacencyMatrix()
        return graph

    def _build_anfis_xor(self) -> Graph:
        """Build ANFIS zero-order Sugeno for XOR (Concurrent mode) to load in GUI.

        This uses `MLPAnfisGraph` (concurrent-style) and `BackpropAnfisGraph` to
        attach gradient wiring. The returned `Graph` is a combined graph suitable
        for opening in the GUI (concurrent processing with buffers).
        """
        # Local imports to avoid GUI import-time side-effects
        from zorvan.Core.BackpropAnfisGraph import BackpropAnfisGraph
        from zorvan.Core.MLPAnfisGraph import MLPAnfisGraph

        # Build ANFIS graph: 2 inputs, 1 output, 2 MFs per input
        anfis = MLPAnfisGraph(numInputs=2, numOutputs=1, mfs_per_input=2)
        anfis.BuildMLP()

        # XOR dataset in row-per-feature form (concurrent mode expects this)
        X = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]
        y = [[0.0, 1.0, 1.0, 0.0]]
        anfis.LoadData(X, y)

        # Attach concurrent backprop adapter for ANFIS
        backprop = BackpropAnfisGraph(anfis, learningRate=0.01)
        backprop.BuildBackprop()

        # Create error buffers for concurrent training (align with output delay)
        try:
            # Buffer size should match dataset size (samples per feature row)
            dataset_size = (
                len(X[0]) if X and hasattr(X, "__iter__") and len(X) > 0 else 6
            )
            anfis.CreateErrorBuffers(bufferSize=dataset_size)
        except Exception:
            # If CreateErrorBuffers missing or fails, ignore; GUI can create error buffers later
            pass

        # Combine graphs into a single Graph object for the GUI
        fullGraph = Graph()
        for node in anfis.nodes:
            fullGraph.AddNode(node)
        for node in backprop.nodes:
            fullGraph.AddNode(node)

        # Starting nodes for concurrent processing: data streams + labels
        fullGraph.starting_nodes = [
            input_pair[0] for input_pair in anfis.inputLayer
        ] + anfis.labelLayer
        fullGraph.UpdateAdjacencyMatrix()

        # Store reference for GUI/debugging if needed
        fullGraph._anfis_graph = anfis

        return fullGraph

    def _build_dejong_ea_elitism(self) -> Graph:
        """Build De Jong EA with elitism - best individual preserved across generations."""
        from zorvan.Nodes.BufferNode import BufferNode
        from zorvan.Nodes.BulkTournamentNode import BulkTournamentNode
        from zorvan.Nodes.DeJongSphereNode import DeJongSphereNode
        from zorvan.Nodes.ElitismNode import ElitismNode
        from zorvan.Nodes.ExtractListElement import ExtractListElement
        from zorvan.Nodes.MutationNode import MutaionNode
        from zorvan.Nodes.PopulationNode import PopulationNode
        from zorvan.Nodes.SequencerNode import SequencerNode
        from zorvan.Nodes.SingleInputCrossover import SingleInputCrossover

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
            auto_generate=True,
        )

        # Population buffer (size 1 to stream individuals)
        populationBuffer = BufferNode("Pop_Buffer", size=1)
        populationBuffer.AddPreNode(populationNode)

        # Fitness evaluation (De Jong sphere function)
        fitnessNode = DeJongSphereNode("Fitness")
        fitnessNode.AddPreNode(populationNode)

        # ELITISM: Track best N individuals from each generation
        num_elites = 1  # Keep top 1 individual(s) - adjustable parameter
        elitismNode = ElitismNode(
            "Elitism", population_size=pop_size, num_elites=num_elites
        )
        elitismNode.AddPreNode(populationBuffer)  # Gets individuals
        elitismNode.AddPreNode(fitnessNode)  # Gets fitness values

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
            num_selections=pop_size
            - num_elites,  # Select fewer to make room for elite individual(s)
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

        graph.UpdateAdjacencyMatrix()
        return graph

    # =========================================================================
    # Forward Processing Examples
    # =========================================================================

    def _build_xor_mlp_forward(self) -> Graph:
        """Build XOR MLP with forward processing (no buffers).

        Uses MLPGraphForwardProcessing which executes nodes in dependency order
        based on the sequence finder algorithm. This is more intuitive for
        understanding neural network forward/backward passes.
        """
        from zorvan.Core.BackpropGraphForwardProcessing import (
            BackpropGraphForwardProcessing,
        )
        from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from zorvan.Nodes.LinearNode import LinearNode

        # Create MLP without buffers (for forward processing)
        mlpGraph = MLPGraphForwardProcessing(
            numInputs=2,
            numOutputs=1,
            numHiddenLayers=1,
            hiddenLayerSizes=[2],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # XOR Dataset - Row-per-sample format for forward processing
        X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
        y = [[0.0], [1.0], [1.0], [0.0]]
        mlpGraph.LoadData(X, y)

        # Add backpropagation
        backprop_graph = BackpropGraphForwardProcessing(mlpGraph, learningRate=0.5)
        backprop_graph.BuildBackprop()

        # Combine graphs
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)

        # Set starting nodes for forward processing (first computation nodes)
        fullGraph.starting_nodes = list(mlpGraph.starting_nodes)

        # Set stopping nodes (weight nodes shouldn't trigger successor activation)
        if hasattr(mlpGraph, "stopping_nodes"):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)
        else:
            fullGraph.stopping_nodes = []

        fullGraph.UpdateAdjacencyMatrix()

        # Store reference to mlpGraph for potential access later
        fullGraph._mlp_graph = mlpGraph

        return fullGraph

    def _build_simple_mlp_forward(self) -> Graph:
        """Build minimal 1x1x1 MLP with forward processing (no buffers).

        Uses MLPGraphForwardProcessing for sequential node execution.
        """
        from zorvan.Core.BackpropGraphForwardProcessing import (
            BackpropGraphForwardProcessing,
        )
        from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from zorvan.Nodes.LinearNode import LinearNode

        mlpGraph = MLPGraphForwardProcessing(
            numInputs=1,
            numOutputs=1,
            numHiddenLayers=1,
            hiddenLayerSizes=[1],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # Load sample data (simple linear relationship) - Row-per-sample format
        X = [[0.0], [0.25], [0.5], [0.75], [1.0]]
        y = [[0.0], [0.25], [0.5], [0.75], [1.0]]
        mlpGraph.LoadData(X, y)

        # Add backpropagation for training
        backprop_graph = BackpropGraphForwardProcessing(mlpGraph, learningRate=0.5)
        backprop_graph.BuildBackprop()

        # Combine graphs
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)

        # Set starting nodes for forward processing
        fullGraph.starting_nodes = (
            list(mlpGraph.starting_nodes) if hasattr(mlpGraph, "starting_nodes") else []
        )

        # Set stopping nodes (weight nodes shouldn't trigger successor activation)
        if hasattr(mlpGraph, "stopping_nodes"):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)
        else:
            fullGraph.stopping_nodes = []

        fullGraph.UpdateAdjacencyMatrix()

        # Store reference to mlpGraph for potential access later
        fullGraph._mlp_graph = mlpGraph
        fullGraph._backprop_graph = backprop_graph

        return fullGraph

    def _build_xor_mlp_forward_bias(self) -> Graph:
        """Build XOR MLP with forward processing and explicit bias nodes enabled."""
        from zorvan.Core.BackpropGraphForwardProcessing import (
            BackpropGraphForwardProcessing,
        )
        from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
        from zorvan.Nodes.LinearNode import LinearNode

        mlpGraph = MLPGraphForwardProcessing(
            numInputs=2,
            numOutputs=1,
            numHiddenLayers=1,
            hiddenLayerSizes=[2],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.add_bias = True
        mlpGraph.BuildMLP()

        X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
        y = [[0.0], [1.0], [1.0], [0.0]]
        mlpGraph.LoadData(X, y)

        backprop_graph = BackpropGraphForwardProcessing(mlpGraph, learningRate=0.5)
        backprop_graph.BuildBackprop()

        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)

        fullGraph.starting_nodes = list(mlpGraph.starting_nodes)
        fullGraph.stopping_nodes = list(getattr(mlpGraph, "stopping_nodes", []))
        fullGraph.UpdateAdjacencyMatrix()
        fullGraph._mlp_graph = mlpGraph
        fullGraph._backprop_graph = backprop_graph

        return fullGraph
