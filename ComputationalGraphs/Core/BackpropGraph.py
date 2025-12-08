from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode


class BackpropGraph(Graph):
    def __init__(self, mlpGraph, learningRate=0.01):
        super().__init__()
        self.mlp_graph = mlpGraph
        self.learning_rate = learningRate

        # Shared layers from MLP graph
        self.inputLayer = mlpGraph.inputLayer
        self.outputLayer = mlpGraph.outputLayer
        self.hiddenLayers = mlpGraph.hiddenLayers
        self.weightLayers = mlpGraph.weightLayers
        self.errorLayer = mlpGraph.errorLayer
        self.errorBuffer = []

        # Backpropagation-specific layers
        self.lrNode = None
        self.errorGradientLayers = (
            []
        )  # Stores gradients of output layer and hidden layers
        self.lrMultiplicationNodes = []  # Mult nodes with learning rate
        self.weightRecalcLayers = []  # Weight adjustment nodes

    def BuildBackprop(self):
        """Build the backpropagation graph by creating LR, gradient, and weight recalculation layers."""
        self._CreateLRNode()
        self._CreateGradientLayers()
        self._CreateWeightRecalculationLayers()
        self._CreateBiasRecalculationLayers()
        self.UpdateAdjacencyMatrix()

    def _CreateLRNode(self):
        """Create a single learning rate node."""
        self.lrNode = DisplayNode(name="LearningRate", value=self.learning_rate)
        self.AddNode(self.lrNode)

    def _CreateGradientLayers(self):
        self._CreateOutputGradientLayer()
        self._CreateHiddenGradientLayer()

    def _CreateHiddenGradientLayer(self):
        for layerNum in range(len(self.hiddenLayers) - 1, -1, -1):
            layerErrorGradients = []
            layerLrMultiplications = []

            for n in range(len(self.hiddenLayers[layerNum])):
                # Derivative node for hidden activation
                dervativeNodeType = self.hiddenLayers[layerNum][n][1].derivative
                hiddenDerivNode = dervativeNodeType(name=f"D_H{layerNum}N{n}")
                hiddenDerivNode.AddPreNode(
                    self.hiddenLayers[layerNum][n][2]
                )  # Adding the buffer node of the layer as the prenode

                # Error gradient for hidden layer node
                hiddenErrorGradNode = MultiplicationNode(name=f"EG_H{layerNum}N{n}")
                hiddenErrorGradNode.AddPreNode(hiddenDerivNode)

                # Sum of weighted gradients from the next layer
                weightedGradientSum = AdditionNode(name=f"WGS_H{layerNum}N{n}")
                weightedGradientSum.forcedBatchProcessing = True

                layersAhead = (len(self.hiddenLayers) + 2) - (layerNum + 2)

                # Collect gradients from connected nodes in the next layer
                nextLayer = (
                    self.errorGradientLayers[0]
                    if layerNum == len(self.hiddenLayers) - 1
                    else self.errorGradientLayers[1]
                )
                for k, gradientNode in enumerate(nextLayer):
                    weightNode = self.weightLayers[layerNum + 1][n][k]
                    weightNodeBuffer = BufferNode(
                        name=f"WNBuff_H{layerNum}WN{n}K{k}", size=(layersAhead * 6) - 1
                    )
                    weightNodeBuffer.AddPreNode(weightNode)

                    weightedGradient = MultiplicationNode(
                        name=f"WG_H{layerNum}N{n}W{k}"
                    )
                    weightedGradient.AddPreNode(weightNodeBuffer)
                    weightedGradient.AddPreNode(gradientNode)
                    weightedGradientSum.AddPreNode(weightedGradient)
                    self.AddNode(weightedGradient, weightNodeBuffer)

                hiddenErrorGradNode.AddPreNode(weightedGradientSum)

                # LR multiplier for hidden gradient
                lrMultNode = MultiplicationNode(name=f"LRMult_H{layerNum}N{n}")
                lrMultNode.AddPreNode(
                    hiddenErrorGradNode, self.lrNode
                )  # FIXED: Connect EG -> LRMult

                layerErrorGradients.append(hiddenErrorGradNode)
                layerLrMultiplications.append(lrMultNode)

                self.AddNode(
                    hiddenDerivNode,
                    hiddenErrorGradNode,
                    weightedGradientSum,
                    lrMultNode,
                )

            self.errorGradientLayers.insert(0, layerErrorGradients)
            self.lrMultiplicationNodes.insert(0, layerLrMultiplications)

    def _CreateOutputGradientLayer(self):
        outputErrorGradients = []
        outputLrMultiplications = []

        for i, (outputAddNode, outputActNode) in enumerate(self.outputLayer):
            # Derivative node for the activation function
            dervativeNodeType = outputActNode.derivative
            derivativeNode = dervativeNodeType(name=f"D_y{i}")
            derivativeNode.AddPreNode(outputActNode)

            # Gradient node (Error * Derivative)
            errorGradientNode = MultiplicationNode(name=f"EG_y{i}")
            errorGradientNode.AddPreNode(derivativeNode, self.errorLayer[i])
            outputErrorGradients.append(errorGradientNode)

            # LR multiplier for the gradient
            lrMultNode = MultiplicationNode(name=f"LRMult_y{i}")
            lrMultNode.AddPreNode(errorGradientNode, self.lrNode)
            outputLrMultiplications.append(lrMultNode)

            self.AddNode(derivativeNode, errorGradientNode, lrMultNode)

        self.errorGradientLayers.insert(0, outputErrorGradients)
        self.lrMultiplicationNodes.insert(0, outputLrMultiplications)

    def _CreateWeightRecalculationLayers(self):
        """Create weight recalculation nodes to update weights based on the gradients."""
        for layerNum, weightLayer in enumerate(self.weightLayers):
            weightRecalcLayer = []

            for i, row in enumerate(weightLayer):
                weightUpdateRow = []

                for j, weight_node in enumerate(row):
                    # Determine the input for the gradient calculation based on layer location
                    layerBufferNode = (
                        self.inputLayer[i][1]
                        if layerNum == 0
                        else self.hiddenLayers[layerNum - 1][i][2]
                    )  # Activation node's buffer

                    # Multiply gradient input with the error gradient scaled by learning rate
                    lrMultiplicationNode = self.lrMultiplicationNodes[layerNum][
                        j
                    ]  # Use corresponding LR multiplication node
                    dW = MultiplicationNode(name=f"dw_L{layerNum}_W{i}{j}")

                    # Connect weight update node to gradient input and the learning rate node
                    dW.AddPreNode(layerBufferNode, lrMultiplicationNode)

                    # Set the result directly into the weight node using ContainerNode's accumulation property
                    weight_node.AddPreNode(dW)

                    # Store nodes for tracking in the recalculation layer
                    weightUpdateRow.append(dW)
                    # self.AddNode(singleDelay)
                    self.AddNode(dW)

                weightRecalcLayer.append(weightUpdateRow)

            self.weightRecalcLayers.append(weightRecalcLayer)

    def _CreateBiasRecalculationLayers(self):
        """Create bias recalculation nodes to update biases based on the gradients.

        Bias gradient is simpler than weight gradient:
        dB = lr * error_gradient (no multiplication by input activation needed)

        The ContainerNode will compute: b_new = b_old - dB

        For concurrent mode timing synchronization, we create a pass-through
        multiplication node (multiply by 1) that acts similarly to dW nodes.
        """
        # Check if MLP has biases
        if not hasattr(self.mlp_graph, "biasLayers") or not self.mlp_graph.biasLayers:
            return

        if not hasattr(self.mlp_graph, "use_bias") or not self.mlp_graph.use_bias:
            return

        from ComputationalGraphs.Nodes.DisplayNode import DisplayNode

        # Create a constant 1.0 node for bias gradient pass-through
        self.biasOneNode = DisplayNode(name="BiasOne", value=1.0)
        self.AddNode(self.biasOneNode)

        self.biasRecalcLayers = []

        for layerNum, biasLayer in enumerate(self.mlp_graph.biasLayers):
            biasRecalcLayer = []

            for j, bias_node in enumerate(biasLayer):
                # Bias gradient is just lr * error_gradient (no input activation multiplication)
                # lrMultiplicationNodes[layerNum][j] already contains lr * error_gradient
                lrMultNode = self.lrMultiplicationNodes[layerNum][j]

                # Create a dB node similar to dW, multiplying by 1.0 for timing sync
                dB = MultiplicationNode(name=f"dB_L{layerNum}N{j}")
                dB.AddPreNode(self.biasOneNode, lrMultNode)

                # Connect dB to bias node - ContainerNode will subtract the gradient
                bias_node.AddPreNode(dB)

                biasRecalcLayer.append(dB)
                self.AddNode(dB)

            self.biasRecalcLayers.append(biasRecalcLayer)
