from Graph import Graph
from MultiplicationNode import MultiplicationNode
from AdditionNode import AdditionNode
from DisplayNode import DisplayNode
from SigmoidDerivativeNode import SigmoidDerivativeNode  # Import custom derivative node
from MeanSquaredErrorNode import MeanSquaredErrorNode

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

        # Backpropagation-specific layers
        self.lrNode = None
        self.errorGradientLayers = []   # Stores gradients of output layer and hidden layers
        self.lrMultiplicationNodes = [] # Mult nodes with learning rate
        self.weightRecalcLayers = []    # Weight adjustment nodes

    def BuildBackprop(self):
        """Build the backpropagation graph by creating LR, gradient, and weight recalculation layers."""
        self._CreateLRNode()
        self._CreateGradientLayers()
        self._CreateWeightRecalculationLayers()
        self.UpdateAdjacencyMatrix()
        
    def _CreateLRNode(self):
        """Create a single learning rate node."""
        self.lrNode = DisplayNode(name="LearningRate", value=self.learning_rate)
        self.AddNode(self.lrNode)

    def _CreateGradientLayers(self):
        """Create gradient layers for backpropagation, handling both the output and hidden layers."""
        
        # Create gradient layer for the output layer
        outputErrorGradients = []
        outputLrMultiplications = []
        
        for i, (outputAddNode, outputActNode) in enumerate(self.outputLayer):
            # Derivative node for the activation function
            derivativeNode = SigmoidDerivativeNode(name=f"SigD_y{i}")
            derivativeNode.AddPreNode(outputActNode)
            
            # Gradient node (Error * Derivative)
            errorGradientNode = MultiplicationNode(name=f"EG_y{i}")
            errorGradientNode.AddPreNode(derivativeNode, self.errorLayer[i])
            outputErrorGradients.append(errorGradientNode)
            
            # LR multiplier for the gradient
            lrMultNode = MultiplicationNode(name=f"LRMult_y{i}")
            lrMultNode.AddPreNode(errorGradientNode,self.lrNode)
            outputLrMultiplications.append(lrMultNode)
            
            self.AddNode(derivativeNode, errorGradientNode, lrMultNode)
        
        self.errorGradientLayers.insert(0, outputErrorGradients)
        self.lrMultiplicationNodes.insert(0, outputLrMultiplications)
        
        # Create gradient layers for each hidden layer in reverse order
        for layerNum in range(len(self.hiddenLayers) - 1, -1, -1):
            layerErrorGradients = []
            layerLrMultiplications = []
            
            for j, (hiddenAddNode, hiddenActNode) in enumerate(self.hiddenLayers[layerNum]):
                # Derivative node for hidden activation
                hiddenDerivNode = SigmoidDerivativeNode(name=f"SigD_H{layerNum}N{j}")
                hiddenDerivNode.AddPreNode(hiddenActNode)
                
                # Error gradient for hidden layer node
                hiddenErrorGradNode = MultiplicationNode(name=f"EG_H{layerNum}N{j}")
                hiddenErrorGradNode.AddPreNode(hiddenDerivNode)
                
                # Sum of weighted gradients from the next layer
                weightedGradientSum = AdditionNode(name=f"WGS_H{layerNum}N{j}")
                
                # Collect gradients from connected nodes in the next layer
                nextLayer = self.errorGradientLayers[0] if layerNum == len(self.hiddenLayers) - 1 else self.errorGradientLayers[1]
                for k, gradientNode in enumerate(nextLayer):
                    weightNode = self.weightLayers[layerNum + 1][j][k]
                    weightedGradient = MultiplicationNode(name=f"WG_H{layerNum}N{j}W{k}")
                    weightedGradient.AddPreNode(weightNode)
                    weightedGradient.AddPreNode(gradientNode)
                    weightedGradientSum.AddPreNode(weightedGradient)
                    self.AddNode(weightedGradient)
                
                hiddenErrorGradNode.AddPreNode(weightedGradientSum)
                
                # LR multiplier for hidden gradient
                lrMultNode = MultiplicationNode(name=f"LRMult_H{layerNum}N{j}")
                lrMultNode.AddPreNode(hiddenErrorGradNode)
                lrMultNode.AddPreNode(self.lrNode)
                
                layerErrorGradients.append(hiddenErrorGradNode)
                layerLrMultiplications.append(lrMultNode)
                
                self.AddNode(hiddenDerivNode, hiddenErrorGradNode, weightedGradientSum, lrMultNode)
            
            self.errorGradientLayers.insert(0, layerErrorGradients)
            self.lrMultiplicationNodes.insert(0, layerLrMultiplications)
    
    def _CreateWeightRecalculationLayers(self):
        """Create weight recalculation nodes to update weights based on the gradients."""
        for layerNum, weightLayer in enumerate(self.weightLayers):
            weightRecalcLayer = []
            
            for i, row in enumerate(weightLayer):
                weightUpdateRow = []
                
                for j, weight_node in enumerate(row):
                    # Determine the input for the gradient calculation based on layer location
                    layerActivationNode = (self.inputLayer[i] if layerNum == 0
                                    else self.hiddenLayers[layerNum - 1][i][1])  # Activation node

                    # Multiply gradient input with the error gradient scaled by learning rate
                    lrMultiplicationNode = self.lrMultiplicationNodes[layerNum][j]  # Use corresponding LR multiplication node
                    dW = MultiplicationNode(name=f"dw_L{layerNum}_W{i}{j}")
                    
                    # Connect weight update node to gradient input and the learning rate node
                    dW.AddPreNode(layerActivationNode, lrMultiplicationNode)
                    
                    # Set the result directly into the weight node using ContainerNode's accumulation property
                    weight_node.AddPreNode(dW)
                    
                    # Store nodes for tracking in the recalculation layer
                    weightUpdateRow.append(dW)
                    self.AddNode(dW)
                    
                weightRecalcLayer.append(weightUpdateRow)
            
            self.weightRecalcLayers.append(weightRecalcLayer)
