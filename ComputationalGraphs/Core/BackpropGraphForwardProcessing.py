"""
BackpropGraphForwardProcessing - Backpropagation for Forward Processing Mode

This module creates backpropagation graphs WITHOUT buffer nodes, designed to work
with MLPGraphForwardProcessing and the ForwardProcessing execution method.

Key differences from BackpropGraph:
- NO BufferNode instances (immediate gradient propagation)
- Direct connections for instant weight updates
- Optimized for iteration-based execution
- Enables "second descent" in training loss

Use this with MLPGraphForwardProcessing for training that matches
classical implementation performance.
"""

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode


class BackpropGraphForwardProcessing(Graph):
    def __init__(self, mlpGraph, learningRate=0.01):
        """
        Initialize backpropagation graph for forward processing (no buffers).

        Args:
            mlpGraph: MLPGraphForwardProcessing instance
            learningRate: Learning rate for gradient descent
        """
        super().__init__()
        self.mlp_graph = mlpGraph
        self.learning_rate = learningRate

        # Shared layers from MLP graph
        self.inputLayer = mlpGraph.inputLayer
        self.outputLayer = mlpGraph.outputLayer
        self.hiddenLayers = mlpGraph.hiddenLayers
        self.weightLayers = mlpGraph.weightLayers
        self.errorLayer = mlpGraph.errorLayer

        # Backpropagation-specific layers
        self.lrNode = None
        self.errorGradientLayers = []
        self.lrMultiplicationNodes = []
        self.weightRecalcLayers = []

    def BuildBackprop(self):
        """Build the backpropagation graph WITHOUT buffers."""
        self._CreateLRNode()
        self._CreateGradientLayers()
        self._CreateWeightRecalculationLayers()
        self._CreateBiasRecalculationLayers()
        self.UpdateAdjacencyMatrix()

        # Clear stopping_nodes so weight successors (gradients) can be sequenced
        # MLPGraph populates stopping_nodes with weights for forward-only execution,
        # but with backprop built, we need the full graph including gradient flows
        self.stopping_nodes = []
        if hasattr(self.mlp_graph, "stopping_nodes"):
            self.mlp_graph.stopping_nodes = []

    def _CreateLRNode(self):
        """Create learning rate node."""
        # Learning rate is a constant hyperparameter for forward processing
        # and should behave like a display/source node so it is available
        # to gradient multipliers without being treated as a mutable weight.
        self.lrNode = DisplayNode(name="LearningRate", value=self.learning_rate)
        self.AddNode(self.lrNode)
        # No separate bias learning rate: forward processing uses the same LR for biases

    def _CreateGradientLayers(self):
        """Create gradient computation layers."""
        self._CreateOutputGradientLayer()
        self._CreateHiddenGradientLayer()

    def _CreateOutputGradientLayer(self):
        """Create output layer gradients (error * derivative)."""
        outputErrorGradients = []
        outputLrMultiplications = []

        for i, (outputAddNode, outputActNode) in enumerate(self.outputLayer):
            # Derivative node for the activation function
            derivativeNodeType = outputActNode.derivative
            derivativeNode = derivativeNodeType(name=f"D_y{i}")
            derivativeNode.AddPreNode(outputActNode)  # Direct connection - no buffer!

            # Gradient node (Error * Derivative)
            errorGradNode = MultiplicationNode(name=f"EG_y{i}")
            errorGradNode.AddPreNode(self.errorLayer[i])  # Error
            errorGradNode.AddPreNode(derivativeNode)  # Derivative

            # LR multiplication node
            lrMultNode = MultiplicationNode(name=f"LRMult_y{i}")
            lrMultNode.AddPreNode(self.lrNode)
            lrMultNode.AddPreNode(errorGradNode)

            outputErrorGradients.append(errorGradNode)
            outputLrMultiplications.append(lrMultNode)

            self.AddNode(derivativeNode, errorGradNode, lrMultNode)

        self.errorGradientLayers.append(outputErrorGradients)
        self.lrMultiplicationNodes.append(outputLrMultiplications)

    def _CreateHiddenGradientLayer(self):
        """Create hidden layer gradients (backpropagate from output)."""
        for layerNum in range(len(self.hiddenLayers) - 1, -1, -1):
            layerErrorGradients = []
            layerLrMultiplications = []

            for n in range(len(self.hiddenLayers[layerNum])):
                # Derivative node for hidden activation
                derivativeNodeType = self.hiddenLayers[layerNum][n][1].derivative
                hiddenDerivNode = derivativeNodeType(name=f"D_H{layerNum}N{n}")
                # Direct connection to activation node - NO BUFFER!
                hiddenDerivNode.AddPreNode(self.hiddenLayers[layerNum][n][1])

                # Sum of weighted gradients from the next layer
                weightedGradientSum = AdditionNode(name=f"WGS_H{layerNum}N{n}")
                weightedGradientSum.forcedBatchProcessing = True

                # Get next layer gradients
                if layerNum == len(self.hiddenLayers) - 1:
                    # Last hidden layer - connect to output gradients
                    nextLayerGradients = self.errorGradientLayers[0]
                else:
                    # Connect to next hidden layer gradients
                    nextLayerGradients = self.errorGradientLayers[-1]

                # Connect to all nodes in next layer through weights
                for k, gradientNode in enumerate(nextLayerGradients):
                    weightNode = self.weightLayers[layerNum + 1][n][k]

                    # Weighted gradient: weight * next_layer_gradient
                    weightedGradient = MultiplicationNode(
                        name=f"WG_H{layerNum}N{n}W{k}"
                    )
                    weightedGradient.AddPreNode(
                        weightNode
                    )  # Direct connection - NO BUFFER!
                    weightedGradient.AddPreNode(gradientNode)

                    weightedGradientSum.AddPreNode(weightedGradient)
                    self.AddNode(weightedGradient)

                # Error gradient for this hidden node
                hiddenErrorGradNode = MultiplicationNode(name=f"EG_H{layerNum}N{n}")
                hiddenErrorGradNode.AddPreNode(hiddenDerivNode)
                hiddenErrorGradNode.AddPreNode(weightedGradientSum)

                # LR multiplier for hidden gradient
                lrMultNode = MultiplicationNode(name=f"LRMult_H{layerNum}N{n}")
                lrMultNode.AddPreNode(self.lrNode)
                lrMultNode.AddPreNode(hiddenErrorGradNode)

                layerErrorGradients.append(hiddenErrorGradNode)
                layerLrMultiplications.append(lrMultNode)

                self.AddNode(
                    hiddenDerivNode,
                    hiddenErrorGradNode,
                    weightedGradientSum,
                    lrMultNode,
                )

            self.errorGradientLayers.append(layerErrorGradients)
            self.lrMultiplicationNodes.append(layerLrMultiplications)

    def _CreateWeightRecalculationLayers(self):
        """Create weight update layers (w_new = w_old - lr * gradient * activation)."""
        # Output layer weights (from last hidden to output)
        self._CreateOutputWeightRecalcLayer()

        # Hidden layer weights
        self._CreateHiddenWeightRecalcLayers()

        # Input layer weights
        self._CreateInputWeightRecalcLayer()

    def _CreateOutputWeightRecalcLayer(self):
        """Update weights from last hidden layer to output layer."""
        lastHiddenLayerNum = len(self.hiddenLayers) - 1
        weightRecalcLayer = []

        for i in range(len(self.hiddenLayers[lastHiddenLayerNum])):
            weightRecalcRow = []
            for j in range(len(self.outputLayer)):
                # Activation from hidden layer (direct connection - NO BUFFER!)
                hiddenActivation = self.hiddenLayers[lastHiddenLayerNum][i][1]

                # LR * gradient
                lrGradient = self.lrMultiplicationNodes[0][j]

                # Weight delta (dW): lr * gradient * activation
                dW = MultiplicationNode(name=f"dW_H{lastHiddenLayerNum}N{i}y{j}")
                dW.AddPreNode(lrGradient)
                dW.AddPreNode(hiddenActivation)

                # Weight update: ContainerNode will compute w_new = w_old - dW
                self.weightLayers[-1][i][j].AddPreNode(dW)

                weightRecalcRow.append(dW)
                self.AddNode(dW)

            weightRecalcLayer.append(weightRecalcRow)

        self.weightRecalcLayers.append(weightRecalcLayer)

    def _CreateHiddenWeightRecalcLayers(self):
        """Update weights between hidden layers."""
        for layerNum in range(len(self.hiddenLayers) - 1, 0, -1):
            weightRecalcLayer = []

            for i in range(len(self.hiddenLayers[layerNum - 1])):
                weightRecalcRow = []
                for j in range(len(self.hiddenLayers[layerNum])):
                    # Activation from previous hidden layer (direct connection!)
                    prevActivation = self.hiddenLayers[layerNum - 1][i][1]

                    # LR * gradient for current layer
                    lrGradient = self.lrMultiplicationNodes[-(layerNum)][j]

                    # Weight delta (dW): lr * gradient * activation
                    dW = MultiplicationNode(name=f"dW_H{layerNum-1}N{i}H{layerNum}N{j}")
                    dW.AddPreNode(lrGradient)
                    dW.AddPreNode(prevActivation)

                    # Weight update: ContainerNode will compute w_new = w_old - dW
                    self.weightLayers[layerNum][i][j].AddPreNode(dW)

                    weightRecalcRow.append(dW)
                    self.AddNode(dW)

                weightRecalcLayer.append(weightRecalcRow)

            self.weightRecalcLayers.append(weightRecalcLayer)

    def _CreateInputWeightRecalcLayer(self):
        """Update weights from input layer to first hidden layer."""
        weightRecalcLayer = []

        for i in range(len(self.inputLayer)):
            weightRecalcRow = []
            for j in range(len(self.hiddenLayers[0])):
                # Input value (direct connection!)
                inputNode = self.inputLayer[i]

                # LR * gradient for first hidden layer
                lrGradient = self.lrMultiplicationNodes[-1][j]

                # Weight delta (dW): lr * gradient * input
                dW = MultiplicationNode(name=f"dW_x{i}H0N{j}")
                dW.AddPreNode(lrGradient)
                dW.AddPreNode(inputNode)

                # Weight update: ContainerNode will compute w_new = w_old - dW
                self.weightLayers[0][i][j].AddPreNode(dW)

                weightRecalcRow.append(dW)
                self.AddNode(dW)

            weightRecalcLayer.append(weightRecalcRow)

        self.weightRecalcLayers.append(weightRecalcLayer)

    def _CreateBiasRecalculationLayers(self):
        """Create bias recalculation connections for forward processing.

        Bias gradient is simpler than weight gradient:
        dB = lr * error_gradient (no multiplication by input activation needed)

        The ContainerNode will compute: b_new = b_old - dB

        In forward processing, we directly connect the lrMultiplicationNode to the bias.
        """
        # Check if MLP has biases
        if not hasattr(self.mlp_graph, "biasLayers") or not self.mlp_graph.biasLayers:
            return

        # Accept either 'use_bias' (older name) or 'add_bias' (current flag)
        if not (
            getattr(self.mlp_graph, "use_bias", False)
            or getattr(self.mlp_graph, "add_bias", False)
        ):
            return

        self.biasRecalcLayers = []

        # Output layer biases (index -1 in biasLayers, index 0 in lrMultiplicationNodes)
        # Hidden layer biases use corresponding indices

        # The biasLayers are stored in order: [hidden_layer_0, hidden_layer_1, ..., output_layer]
        # The lrMultiplicationNodes are stored in order: [output_layer, hidden_layer_n-1, ..., hidden_layer_0]
        # after _CreateOutputGradientLayer and _CreateHiddenGradientLayer

        for layerNum, biasLayer in enumerate(self.mlp_graph.biasLayers):
            biasRecalcLayer = []

            # Map biasLayers index to lrMultiplicationNodes index
            # biasLayers: [H0, H1, ..., Hn, Output]
            # lrMultiplicationNodes after construction: [Output, Hn, ..., H1, H0]
            # So for hidden layer i: lrMultiplicationNodes index is -(i+1) which is len - 1 - i
            # For output layer (last in biasLayers): lrMultiplicationNodes index is 0

            if layerNum == len(self.mlp_graph.biasLayers) - 1:
                # Output layer biases
                lrMultIndex = 0
            else:
                # Hidden layer biases
                # lrMultiplicationNodes[-1] is first hidden layer (H0)
                # lrMultiplicationNodes[-(n)] is hidden layer n-1
                lrMultIndex = -(layerNum + 1)

            for j, bias_node in enumerate(biasLayer):
                # Bias gradient is just lr * error_gradient (no input activation multiplication)
                lrMultNode = self.lrMultiplicationNodes[lrMultIndex][j]
                # Apply bias scale multiplier to lrMultNode
                from ComputationalGraphs.Nodes.MultiplicationNode import (
                    MultiplicationNode,
                )

                # Connect lrMultNode directly to bias node (no scaling)
                bias_node.AddPreNode(lrMultNode)

                biasRecalcLayer.append(lrMultNode)

            self.biasRecalcLayers.append(biasRecalcLayer)

    @staticmethod
    def RemoveBackpropFromGraph(graph):
        """Remove typical backpropagation nodes from a graph by name patterns (forward processing)."""
        import re

        patterns = [
            r"^EG_",
            r"^LRMult_",
            r"^WG_",
            r"^dW_",
            r"^dB_",
            r"^WGS_",
            r"^D_y",
            r"^D_H",
            r"^BiasOne$",
            r"^LearningRate$",
        ]

        to_remove = []
        for node in list(graph.nodes):
            name = getattr(node, "name", "")
            if any(re.search(p, name) for p in patterns):
                to_remove.append(node)

        for node in to_remove:
            try:
                graph.RemoveNode(node)
            except Exception:
                pass

        graph.UpdateAdjacencyMatrix()
