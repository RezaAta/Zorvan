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
        self.UpdateAdjacencyMatrix()

    def _CreateLRNode(self):
        """Create learning rate node."""
        # Learning rate is a constant hyperparameter for forward processing
        # and should behave like a display/source node so it is available
        # to gradient multipliers without being treated as a mutable weight.
        self.lrNode = DisplayNode(name="LearningRate", value=self.learning_rate)
        self.AddNode(self.lrNode)

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
