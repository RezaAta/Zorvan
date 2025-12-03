"""Example graphs loader for the GUI."""

from typing import Callable, List

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.DivisionNode import DivisionNode
from ComputationalGraphs.Nodes.MaxNode import MaxNode
from ComputationalGraphs.Nodes.MinNode import MinNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
from ComputationalGraphs.Nodes.PiecewiseLinearNode import PiecewiseLinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode


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
        self.categories["basic"] = basic

        # Neural Network Examples (All unified to Concurrent MLP)
        nn_forward = ExampleCategory(
            "Neural Networks", "All MLP examples use the concurrent MLP with buffers"
        )
        nn_forward.add_example(
            "XOR Problem (2-2-1)",
            "2-input XOR with 2-neuron hidden layer using sigmoid activation",
            self._build_xor_mlp_concurrent,
        )
        nn_forward.add_example(
            "Simple MLP (1-1-1)",
            "Minimal MLP for understanding the architecture",
            self._build_simple_mlp_concurrent,
        )
        nn_forward.add_example(
            "Iris Classification (4-5-3-3)",
            "Multi-class classification with two hidden layers",
            self._build_iris_mlp_concurrent,
        )
        self.categories["neural_networks"] = nn_forward

        # Concurrent Processing Neural Network Examples
        nn_concurrent = ExampleCategory(
            "Neural Networks - Concurrent Processing",
            "MLP with concurrent processing (with buffers)",
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
            "Diabetes Prediction (Concurrent)",
            "Regression on the Diabetes dataset using a concurrent MLP with backprop",
            self._build_diabetes_mlp_concurrent,
        )
        nn_concurrent.add_example(
            "Piecewise Function MLP (Concurrent)",
            "Regression on a simple hybrid piecewise function - 1-in 1-out MLP with a 3-neuron hidden layer (Sigmoid)",
            self._build_piecewise_mlp_concurrent,
        )
        nn_concurrent.add_example(
            "Piecewise Function 2 MLP (Concurrent)",
            "Regression on piecewise quadratic / linear function - 1-in, 2-hidden layers (3 ReLU, 8 ReLU)",
            self._build_piecewise_mlp2_concurrent,
        )
        self.categories["neural_networks_concurrent"] = nn_concurrent

        # Manual Processing Neural Network Examples
        nn_manual = ExampleCategory(
            "Neural Networks - Manual Processing",
            "Manual execution sequence for a concurrent MLP",
        )
        nn_manual.add_example(
            "XOR Problem (2-2-1) - Manual",
            "2-input XOR with 2-neuron hidden layer using a predefined manual processing sequence (concurrent)",
            self._build_xor_mlp_manual,
        )
        self.categories["neural_networks_manual"] = nn_manual

        # Fuzzy System Examples
        fuzzy = ExampleCategory("Fuzzy Systems", "Fuzzy logic control systems")
        fuzzy.add_example(
            "Temperature Control (Fan Speed)",
            "Fan speed control based on temperature and humidity using Mamdani fuzzy rules",
            self._build_temperature_control,
        )
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

    def _build_xor_mlp(self) -> Graph:
        """Build XOR MLP with backpropagation (Forward Processing version)."""
        from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
        from ComputationalGraphs.Core.MLPGraph import MLPGraph
        from ComputationalGraphs.Nodes.LinearNode import LinearNode

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
            fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
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
        from ComputationalGraphs.Core.MLPGraphForwardProcessing import (
            MLPGraphForwardProcessing,
        )
        from ComputationalGraphs.Nodes.LinearNode import LinearNode

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
        from ComputationalGraphs.Core.BackpropGraphForwardProcessing import (
            BackpropGraphForwardProcessing,
        )
        from ComputationalGraphs.Core.MLPGraphForwardProcessing import (
            MLPGraphForwardProcessing,
        )
        from ComputationalGraphs.Nodes.LinearNode import LinearNode

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
            fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
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

        from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
        from ComputationalGraphs.Core.MLPGraph import MLPGraph
        from ComputationalGraphs.Nodes.LinearNode import LinearNode

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
            fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
            fullGraph.AddNode(mse)

        # Set starting nodes for concurrent processing: data streams + labels
        fullGraph.starting_nodes = [
            input_pair[0] for input_pair in mlpGraph.inputLayer
        ] + mlpGraph.labelLayer
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
        hot = PiecewiseLinearNode(
            "Hot", xs=[-20, 5, 25, 45, 100], mus=[0.0, 0.0, 0.5, 1.0, 1.0]
        )
        hot.AddPreNode(temperature)
        cold = PiecewiseLinearNode(
            "Cold", xs=[-20, 5, 25, 45, 100], mus=[1.0, 1.0, 0.5, 0.0, 0.0]
        )
        cold.AddPreNode(temperature)

        # Humidity membership functions
        high_hum = PiecewiseLinearNode(
            "High_Humidity", xs=[0, 25, 50, 75, 100], mus=[0.0, 0.0, 0.5, 1.0, 1.0]
        )
        high_hum.AddPreNode(humidity)
        low_hum = PiecewiseLinearNode(
            "Low_Humidity", xs=[0, 25, 50, 75, 100], mus=[1.0, 1.0, 0.5, 0.0, 0.0]
        )
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
        from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
        from ComputationalGraphs.Core.MLPGraph import MLPGraph
        from ComputationalGraphs.Nodes.LinearNode import LinearNode

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
            fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
            fullGraph.AddNode(mse)

        # Set starting nodes for concurrent processing (data stream nodes + labels)
        fullGraph.starting_nodes = [
            input[0] for input in mlpGraph.inputLayer
        ] + mlpGraph.labelLayer
        fullGraph.UpdateAdjacencyMatrix()

        # Store reference to mlpGraph for potential error buffer creation later
        fullGraph._mlp_graph = mlpGraph

        return fullGraph

    def _build_piecewise_mlp_concurrent(self) -> Graph:
        """Build a small 1-input concurrent MLP that learns a hybrid piecewise function.

        The function is defined as:
            f(x) = sin(x) for x < 0
            f(x) = 0 for 0 ≤ x < 1
            f(x) = 2x + 1 for x ≥ 1

        This builds a concurrent `MLPGraph` with 1 input, 1 hidden layer of 3 Sigmoid neurons,
        and 1 linear output node. It loads a synthetic dataset in row-per-feature format, attaches
        concurrent `BackpropGraph`, and returns a combined `Graph` for the GUI.
        """
        # Local imports (avoid GUI import-time side-effects)
        import numpy as np

        from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
        from ComputationalGraphs.Core.MLPGraph import MLPGraph
        from ComputationalGraphs.Nodes.LinearNode import LinearNode
        from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode

        # Generate dataset for piecewise function
        x_vals = np.linspace(-3.0, 4.0, 300)
        # Piecewise function implementation
        y_vals = np.where(
            x_vals < 0, np.sin(x_vals), np.where(x_vals < 1, 0.0, 2.0 * x_vals + 1.0)
        )

        # Convert to row-per-feature format for concurrent MLPGraph (features, samples)
        X = [x_vals.tolist()]
        y = [y_vals.tolist()]

        # Build concurrent MLPGraph: 1 input -> 3 hidden sigmoid neurons -> 1 linear output
        mlpGraph = MLPGraph(
            numInputs=1,
            numOutputs=1,
            numHiddenLayers=1,
            hiddenLayerSizes=[3],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # Load dataset into the MLP
        mlpGraph.LoadData(X, y)

        # Build concurrent Backprop and attach
        backprop_graph = BackpropGraph(mlpGraph, learningRate=0.01)
        backprop_graph.BuildBackprop()

        # Create error buffers and MSE nodes for plotting
        mlpGraph.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X[0]))

        # Combine into a single Graph for the GUI
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        # Add error buffers and MSE nodes to the full graph
        for eb in mlpGraph.errorBuffers:
            fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
            fullGraph.AddNode(mse)

        # Set starting nodes for concurrent processing: data streams + labels
        fullGraph.starting_nodes = [
            input_pair[0] for input_pair in mlpGraph.inputLayer
        ] + mlpGraph.labelLayer

        # Copy stopping nodes (weights) so GUI/processor can respect them
        if hasattr(mlpGraph, "stopping_nodes"):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)

        fullGraph.UpdateAdjacencyMatrix()

        # Store references for GUI debug/controls
        fullGraph._mlp_graph = mlpGraph
        fullGraph._backprop_graph = backprop_graph

        return fullGraph

    def _build_piecewise_mlp2_concurrent(self) -> Graph:
        """Build a concurrent MLP that learns the quadratic-linear piecewise function.

        f(x) = x^2 for x < 0
        f(x) = 0 for 0 <= x <= 1
        f(x) = 2x + 1 for x > 1

        Architecture: 1 input -> [3 ReLU] -> [8 ReLU] -> 1 Linear output; concurrent MLP with buffers.
        """
        import numpy as np

        from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
        from ComputationalGraphs.Core.MLPGraph import MLPGraph
        from ComputationalGraphs.Nodes.LinearNode import LinearNode
        from ComputationalGraphs.Nodes.ReLUNode import ReLUNode

        # Create dataset
        x_vals = np.linspace(-3.0, 4.0, 300)
        y_vals = np.where(
            x_vals < 0, x_vals**2, np.where(x_vals <= 1, 0.0, 2.0 * x_vals + 1.0)
        )

        # Convert to row-per-feature format for concurrent MLPGraph
        X = [x_vals.tolist()]
        y = [y_vals.tolist()]

        # Build concurrent MLPGraph with specified architecture
        mlpGraph = MLPGraph(
            numInputs=1,
            numOutputs=1,
            numHiddenLayers=2,
            hiddenLayerSizes=[3, 8],
            activationFunction=ReLUNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        mlpGraph.LoadData(X, y)

        backprop_graph = BackpropGraph(mlpGraph, learningRate=0.001)
        backprop_graph.BuildBackprop()

        # Create error buffers and MSE nodes for plotting
        mlpGraph.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X[0]))

        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        # Add error buffers and MSE nodes to the full graph
        for eb in mlpGraph.errorBuffers:
            fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
            fullGraph.AddNode(mse)

        fullGraph.starting_nodes = [
            input_pair[0] for input_pair in mlpGraph.inputLayer
        ] + mlpGraph.labelLayer
        if hasattr(mlpGraph, "stopping_nodes"):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)

        fullGraph.UpdateAdjacencyMatrix()
        fullGraph._mlp_graph = mlpGraph
        fullGraph._backprop_graph = backprop_graph

        return fullGraph

    def _build_xor_mlp_manual(self) -> Graph:
        """Build XOR MLP wired for ManualProcessing with a predefined sequence.

        This constructs a forward-processing MLP with backprop, combines both
        graphs into a single `Graph` and assigns `manual_processing_sequence`
        so the GUI/manual controller can call `GraphProcessor.ManualProcessing`
        without needing to compute the sequence interactively.
        """
        from ComputationalGraphs.Core.BackpropGraphForwardProcessing import (
            BackpropGraphForwardProcessing,
        )
        from ComputationalGraphs.Core.MLPGraphForwardProcessing import (
            MLPGraphForwardProcessing,
        )
        from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
        from ComputationalGraphs.Nodes.LinearNode import LinearNode

        # Build MLP (concurrent style)
        mlpGraph = MLPGraph(
            numInputs=2,
            numOutputs=1,
            numHiddenLayers=1,
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # Load XOR dataset (row-per-sample format expected by forward processing)
        X_train = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
        y_train = [[0.0], [1.0], [1.0], [0.0]]
        mlpGraph.LoadData(X_train, y_train)

        # Attach backprop (concurrent variant)
        backprop_graph = BackpropGraph(mlpGraph, learningRate=0.5)
        backprop_graph.BuildBackprop()

        # Combine graphs into a single Graph for GUI
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)

        # Prepare a manual, explicit processing sequence.
        # Sequence groups are ordered to perform: forward multiplies -> additions -> activations -> output -> error -> derivatives -> gradients -> lr multipliers -> weight deltas -> weight container updates
        sequence = []

        # 1) First-layer multiplications (input * weights)
        first_mults = [
            n for n in fullGraph.nodes if getattr(n, "name", "").startswith("Mul_x")
        ]
        sequence.append(first_mults)

        # 2) Hidden layer additions
        hidden_adds = [h[0] for h in mlpGraph.hiddenLayers[0]]
        sequence.append(hidden_adds)

        # 3) Hidden activations
        hidden_acts = [h[1] for h in mlpGraph.hiddenLayers[0]]
        sequence.append(hidden_acts)

        # 4) Multiplications into output (last hidden -> output)
        output_mults = []
        for out_add, out_act in mlpGraph.outputLayer:
            # predecessors of output addition are the multiplication nodes
            for pred in out_add.predecessors:
                if pred not in output_mults:
                    output_mults.append(pred)
        sequence.append(output_mults)

        # 5) Output additions
        out_adds = [out[0] for out in mlpGraph.outputLayer]
        sequence.append(out_adds)

        # 6) Output activations
        out_acts = [out[1] for out in mlpGraph.outputLayer]
        sequence.append(out_acts)

        # 7) Error calculation nodes
        sequence.append(list(mlpGraph.errorLayer))

        # Backprop-related groups: derive from backprop_graph nodes
        # 8) Output derivative nodes (D_y...)
        dy_nodes = [
            n for n in backprop_graph.nodes if getattr(n, "name", "").startswith("D_y")
        ]
        if dy_nodes:
            sequence.append(dy_nodes)

        # 9) Output error-gradient nodes (EG_y...)
        eg_output = [
            n for n in backprop_graph.nodes if getattr(n, "name", "").startswith("EG_y")
        ]
        if eg_output:
            sequence.append(eg_output)

        # 10) LR multipliers for outputs
        lr_y = [
            n
            for n in backprop_graph.nodes
            if getattr(n, "name", "").startswith("LRMult_y")
        ]
        if lr_y:
            sequence.append(lr_y)

        # 11) Hidden derivative and weighted-gradient-sum nodes (hidden grad accumulation)
        d_hidden = [
            n for n in backprop_graph.nodes if getattr(n, "name", "").startswith("D_H")
        ]
        wgs_nodes = [
            n
            for n in backprop_graph.nodes
            if getattr(n, "name", "").startswith("WGS_H")
        ]
        if wgs_nodes:
            sequence.append(wgs_nodes)
        if d_hidden:
            sequence.append(d_hidden)

        # 12) Hidden error-gradient nodes (EG_H...)
        eg_hidden = [
            n for n in backprop_graph.nodes if getattr(n, "name", "").startswith("EG_H")
        ]
        if eg_hidden:
            sequence.append(eg_hidden)

        # 13) LR multipliers for hidden nodes
        lr_hidden = [
            n
            for n in backprop_graph.nodes
            if getattr(n, "name", "").startswith("LRMult_H")
        ]
        if lr_hidden:
            sequence.append(lr_hidden)

        # 14) Weight delta nodes (dW_*) produced by weight recalculation layers
        dws = [
            n for n in backprop_graph.nodes if getattr(n, "name", "").startswith("dW_")
        ]
        if dws:
            sequence.append(dws)

        # 15) Finally, include Container weight nodes so they process their incoming dW updates
        # Include all container weights (both stopping and non-stopping) and deduplicate
        container_weights = []
        for n in fullGraph.nodes:
            if isinstance(n, ContainerNode):
                container_weights.append(n)
        # also append stopping_nodes (weights) to ensure updates occur
        try:
            container_weights += [
                n
                for n in getattr(mlpGraph, "stopping_nodes", [])
                if isinstance(n, ContainerNode)
            ]
        except Exception:
            pass
        if container_weights:
            sequence.append(container_weights)

        # 16) Advance input streams and label nodes AFTER weight updates so the next
        # sample is read for the next manual sequence cycle. This ensures the
        # network doesn't get stuck on the initial sample.
        input_nodes = list(mlpGraph.inputLayer)
        label_nodes = list(mlpGraph.labelLayer)
        if input_nodes or label_nodes:
            sequence.append(input_nodes + label_nodes)

        # Compress the sequence to match the MLP graph pass length so that
        # DataStreamNodes are executed once per training pass. This keeps the
        # manual sequence aligned with `mlpGraph.GetPassLength()` used by
        # Reactivation/forward processing logic.
        try:
            pass_len = mlpGraph.GetPassLength()
            if pass_len and len(sequence) > pass_len:
                # Build successor and predecessor maps for conflict detection
                successor_map = fullGraph.BuildSuccessorMap()
                predecessor_map = {
                    node: set(node.predecessors) for node in fullGraph.nodes
                }

                # Merge adjacent original steps into groups, avoiding intra-group dependencies
                groups = []
                cur_group = []
                cur_set = set()
                for step in sequence:
                    # Check if adding this step would cause a dependency conflict
                    conflict = False
                    for n in step:
                        if any(
                            pred in cur_set for pred in predecessor_map.get(n, set())
                        ):
                            conflict = True
                            break
                        if any(succ in cur_set for succ in successor_map.get(n, [])):
                            conflict = True
                            break
                    if conflict:
                        if cur_group:
                            groups.append(cur_group)
                        cur_group = list(step)
                        cur_set = set(step)
                    else:
                        for n in step:
                            if n not in cur_set:
                                cur_group.append(n)
                                cur_set.add(n)
                if cur_group:
                    groups.append(cur_group)

                # If groups exceed pass_len, attempt to merge adjacent safe groups
                while len(groups) > pass_len:
                    merged_any = False
                    for i in range(len(groups) - 1):
                        g1 = groups[i]
                        g2 = groups[i + 1]
                        # Check whether any node in g1 is predecessor/successor of node in g2
                        safe = True
                        for a in g1:
                            for b in g2:
                                if a in predecessor_map.get(
                                    b, set()
                                ) or a in successor_map.get(b, []):
                                    safe = False
                                    break
                            if not safe:
                                break
                        if safe:
                            groups[i] = g1 + g2
                            del groups[i + 1]
                            merged_any = True
                            break
                    if not merged_any:
                        # Cannot merge further without violating dependencies; break
                        break

                # If groups < pass_len, attempt to split larger groups while preserving no intra-group dependencies
                while len(groups) < pass_len:
                    # Find a group with 2+ nodes to split
                    split_idx = next(
                        (i for i, g in enumerate(groups) if len(g) > 1), None
                    )
                    if split_idx is None:
                        break
                    g = groups[split_idx]
                    split_done = False
                    # Try to find a pivot where left has no successors in right (no dependencies across split)
                    for pivot in range(1, len(g)):
                        left = g[:pivot]
                        right = g[pivot:]
                        ok = True
                        for a in left:
                            for b in right:
                                if a in predecessor_map.get(
                                    b, set()
                                ) or a in successor_map.get(b, []):
                                    ok = False
                                    break
                            if not ok:
                                break
                        if ok:
                            groups[split_idx : split_idx + 1] = [left, right]
                            split_done = True
                            break
                    if not split_done:
                        break

                sequence = groups
        except Exception:
            # If anything fails, keep the original sequence
            pass

        # Assign the manual processing sequence on the graph (use Node objects)
        fullGraph.set_manual_processing_sequence(sequence, strict=True)
        # Store the manual pass length so GUI/consumers know how many iterations are
        # required for a complete manual pass (each group is one iteration).
        fullGraph.manual_pass_length = len(sequence)

        # Set starting nodes for concurrent GUI expectations (data streams + labels)
        fullGraph.starting_nodes = [
            input_pair[0] for input_pair in mlpGraph.inputLayer
        ] + mlpGraph.labelLayer
        # Copy stopping nodes (weights) so GUI/processor can respect them
        if hasattr(mlpGraph, "stopping_nodes"):
            fullGraph.stopping_nodes = list(mlpGraph.stopping_nodes)

        fullGraph.UpdateAdjacencyMatrix()

        # Store references for debugging/UI
        fullGraph._mlp_graph = mlpGraph
        fullGraph._backprop_graph = backprop_graph

        return fullGraph

    def _build_diabetes_mlp_concurrent(self) -> Graph:
        """Build Diabetes regression MLP (Concurrent Processing with buffers).

        This adapts the test script `TestingOnDiabetes.py` into a GUI-loadable
        example. It loads the sklearn Diabetes dataset, removes outliers via IQR,
        scales features, then builds a concurrent `MLPGraph` and `BackpropGraph`.

        NOTE: Error buffers are NOT added here; the GUI runner can create them
        after a warmup if needed (similar to other concurrent examples).
        """
        # Local imports to avoid GUI import-time side-effects
        import numpy as np
        from sklearn.datasets import load_diabetes
        from sklearn.preprocessing import StandardScaler

        from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
        from ComputationalGraphs.Core.MLPGraph import MLPGraph
        from ComputationalGraphs.Nodes.LinearNode import LinearNode

        # Load Diabetes Dataset
        data = load_diabetes()
        inputData = data.data  # Features (n_samples, n_features)
        targetData = data.target  # (n_samples,)

        # Detect and remove outliers using IQR on target
        q1 = np.percentile(targetData, 25, axis=0)
        q3 = np.percentile(targetData, 75, axis=0)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        non_outlier_mask = (targetData >= lower_bound) & (targetData <= upper_bound)
        inputData = inputData[non_outlier_mask.flatten()]
        targetData = targetData[non_outlier_mask.flatten()]

        # Reshape target and scale features
        targetData = targetData.reshape(-1, 1)
        scaler = StandardScaler()
        inputData = scaler.fit_transform(inputData)

        # Convert to row-per-feature format expected by concurrent MLPGraph
        X = inputData.T.tolist()  # shape: (features, samples)
        y = targetData.T.tolist()  # shape: (1, samples)

        # Build concurrent MLPGraph
        mlpGraph = MLPGraph(
            numInputs=len(X),
            numOutputs=1,
            numHiddenLayers=3,
            hiddenLayerSizes=[8, 4, 2],
            activationFunction=SigmoidNode,
            outputLayerType=LinearNode,
        )
        mlpGraph.BuildMLP()

        # Attach concurrent backprop
        backprop_graph = BackpropGraph(mlpGraph, learningRate=0.00001)
        backprop_graph.BuildBackprop()

        # Load dataset into the graph
        mlpGraph.LoadData(X, y)

        # Create error buffers and MSE nodes for plotting
        mlpGraph.CreateErrorBuffers(bufferSize=100, mse_buffer_size=len(X[0]))

        # Combine graphs into a single Graph object for the GUI
        fullGraph = Graph()
        for node in mlpGraph.nodes:
            fullGraph.AddNode(node)
        for node in backprop_graph.nodes:
            fullGraph.AddNode(node)
        # Add error buffers and MSE nodes to the full graph
        for eb in mlpGraph.errorBuffers:
            fullGraph.AddNode(eb)
        for mse in mlpGraph.mseNodes:
            fullGraph.AddNode(mse)

        # Starting nodes for concurrent processing: data streams + labels
        fullGraph.starting_nodes = [
            input_pair[0] for input_pair in mlpGraph.inputLayer
        ] + mlpGraph.labelLayer
        fullGraph.UpdateAdjacencyMatrix()

        # Store reference for GUI/debugging if needed
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
        from ComputationalGraphs.Nodes.BufferNode import BufferNode
        from ComputationalGraphs.Nodes.BulkTournamentNode import BulkTournamentNode
        from ComputationalGraphs.Nodes.DeJongSphereNode import DeJongSphereNode
        from ComputationalGraphs.Nodes.ExtractListElement import ExtractListElement
        from ComputationalGraphs.Nodes.MutationNode import MutaionNode
        from ComputationalGraphs.Nodes.PopulationNode import PopulationNode
        from ComputationalGraphs.Nodes.SequencerNode import SequencerNode
        from ComputationalGraphs.Nodes.SingleInputCrossover import SingleInputCrossover

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
        from ComputationalGraphs.Core.BackpropAnfisGraph import BackpropAnfisGraph
        from ComputationalGraphs.Core.MLPAnfisGraph import MLPAnfisGraph

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
            dataset_size = len(X[0]) if X and hasattr(X, '__iter__') and len(X) > 0 else 6
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
        from ComputationalGraphs.Nodes.BufferNode import BufferNode
        from ComputationalGraphs.Nodes.BulkTournamentNode import BulkTournamentNode
        from ComputationalGraphs.Nodes.DeJongSphereNode import DeJongSphereNode
        from ComputationalGraphs.Nodes.ElitismNode import ElitismNode
        from ComputationalGraphs.Nodes.ExtractListElement import ExtractListElement
        from ComputationalGraphs.Nodes.MutationNode import MutaionNode
        from ComputationalGraphs.Nodes.PopulationNode import PopulationNode
        from ComputationalGraphs.Nodes.SequencerNode import SequencerNode
        from ComputationalGraphs.Nodes.SingleInputCrossover import SingleInputCrossover

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
