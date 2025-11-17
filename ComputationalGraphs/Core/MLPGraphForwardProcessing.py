"""
MLPGraphForwardProcessing - MLP for Forward Processing Mode

This module creates MLP graphs WITHOUT buffer nodes, designed to work
with the ForwardProcessing execution method.

Key differences from MLPGraph:
- NO BufferNode instances (immediate value propagation)
- NO delays in label layer (synchronous training)
- Optimized for iteration-based execution
- Compatible with immediate gradient application

Use this for neural network training where you want to eliminate
temporal delays and achieve performance comparable to classical implementations.
"""

import random
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
from ComputationalGraphs.Nodes.SubtractionNode import SubtractionNode

class MLPGraphForwardProcessing(Graph):
    def __init__(self, numInputs, numOutputs, numHiddenLayers, 
                 activationFunction=SigmoidNode, hiddenLayerSizes=None, 
                 outputLayerType=LinearNode):
        """
        Initialize MLP for forward processing (no buffers).
        
        Args:
            numInputs: Number of input features
            numOutputs: Number of output nodes
            numHiddenLayers: Number of hidden layers
            activationFunction: Activation function class (default: SigmoidNode)
            hiddenLayerSizes: List of neurons per hidden layer (default: all same as numInputs)
            outputLayerType: Output layer activation (default: LinearNode)
        """
        super().__init__()
        self.numInputs = numInputs
        self.numOutputs = numOutputs
        self.numHiddenLayers = numHiddenLayers
        self.activationFunction = activationFunction
        self.hiddenLayerSizes = hiddenLayerSizes if hiddenLayerSizes else [numInputs] * numHiddenLayers
        self.outputLayerFunction = outputLayerType
        
        self.inputLayer = []
        self.outputLayer = []
        self.hiddenLayers = []
        self.weightLayers = []
        self.labelLayer = []
        self.errorLayer = []
        self.errorBuffers = []
        # Nodes for which successor candidation should be suppressed when processed
        # (used to prevent weights from initiating successor activation)
        self.stopping_nodes = []

    def BuildMLP(self):
        """Build the MLP architecture WITHOUT buffers for forward processing."""
        self._CreateInputLayer()
        self._CreateHiddenLayers()
        self._CreateOutputLayer()
        self._CreateWeightLayers()
        self._CreateLabelLayer()
        self._CreateErrorLayer()
        
        # Connect layers (stores first layer multiplication nodes)
        self._ConnectInputLayer()
        self._ConnectHiddenLayers()
        self._ConnectOutputLayer()
        self.UpdateAdjacencyMatrix()
        
        # Set starting nodes for forward processing execution
        # The FIRST COMPUTATION in the network is multiplication of inputs and weights
        # These multiplication nodes should be the starting nodes, not inputs/weights themselves!
        # Inputs and weights already have values (from LoadData and initialization)
        # Multiplication nodes READ those values and perform the first computation
        # Labels are NOT starting nodes - they're just data holders read by Error nodes
        self.starting_nodes = self.firstLayerMultNodes

    def LoadData(self, X_data, y_data):
        """
        Load entire dataset into the network's DataStreamNodes.
        
        The DataStreamNodes will automatically cycle through samples as their
        Operation() method is called during processing.
        
        Args:
            X_data: List of input samples [[x1_1, x1_2, ...], [x2_1, x2_2, ...], ...]
                    Each inner list is one sample, shape: (num_samples, num_inputs)
            y_data: List of label samples [[y1_1, ...], [y2_1, ...], ...]
                    Each inner list is one sample, shape: (num_samples, num_outputs)
        """
        if len(X_data) == 0 or len(y_data) == 0:
            raise ValueError("Data cannot be empty")
        
        # Check if X_data[0] is iterable (list of samples) or single value
        if not hasattr(X_data[0], '__iter__'):
            # Single sample provided as [x1, x2, ...], wrap it
            X_data = [X_data]
            y_data = [y_data]
        
        if len(X_data[0]) != self.numInputs:
            raise ValueError(f"X_data feature count {len(X_data[0])} must match numInputs {self.numInputs}")
        if len(y_data[0]) != self.numOutputs:
            raise ValueError(f"y_data feature count {len(y_data[0])} must match numOutputs {self.numOutputs}")
        
        # Load data into DataStreamNodes - each feature node gets its column of data
        for i in range(self.numInputs):
            # Extract column i from all samples
            feature_column = [sample[i] for sample in X_data]
            self.inputLayer[i].data = feature_column
            self.inputLayer[i].value = feature_column[0]  # Initialize with first value
            self.inputLayer[i].iteration = 0  # Reset iteration counter
            self.inputLayer[i].streamIndex = 0  # Reset stream position
            self.inputLayer[i].lastStream = 0  # Reset last stream time
        
        for i in range(self.numOutputs):
            # Extract column i from all labels
            label_column = [sample[i] for sample in y_data]
            self.labelLayer[i].data = label_column
            self.labelLayer[i].value = label_column[0]  # Initialize with first value
            self.labelLayer[i].iteration = 0  # Reset iteration counter
            self.labelLayer[i].streamIndex = 0  # Reset stream position
            self.labelLayer[i].lastStream = 0  # Reset last stream time
    
    def PrepareForForwardProcessing(self, processor):
        """
        Prepare the MLP graph for forward processing by marking source nodes as processed.
        
        This solves the "branch processing issue" where starting nodes (first layer mult nodes)
        need to access source nodes (inputs, weights) that haven't been "processed" yet
        but already have values.
        
        Marks as processed:
        - Input DataStreamNodes (have data loaded) - source nodes
        - Label DataStreamNodes (have data loaded) - source nodes
        - Weight ContainerNodes (have initialized values) - may have dW predecessors after backprop
        
        Call this AFTER LoadData() and AFTER adding backprop (if training), BEFORE starting forward processing.
        
        Args:
            processor: GraphProcessor instance that will execute this graph
            
        Returns:
            tuple: (source_count, container_count) - number of nodes marked
            
        Example usage:
            mlp = MLPGraphForwardProcessing(...)
            mlp.BuildMLP()
            mlp.LoadData(X, y)
            backprop = BackpropGraphForwardProcessing(mlp, ...)
            backprop.BuildBackprop()
            
            processor = GraphProcessor(mlp)
            mlp.PrepareForForwardProcessing(processor)  # Mark sources and weights as processed
            
            for epoch in range(epochs):
                processor.ForwardProcessing(iterations=iterations_per_epoch)
        """
        source_count = processor.mark_source_nodes_as_processed()

        # Also mark container (weight) nodes as processed so the FIRST forward
        # iteration can read weight values even when backprop has added predecessors
        # to those ContainerNodes. This aligns with the intended design: weights
        # are counted as processed for readiness but their usual successor-driven
        # activation is suppressed via `stopping_nodes` to avoid loop reactivation.
        try:
            container_count = 0
            if hasattr(processor, 'mark_container_nodes_as_processed'):
                try:
                    container_count = processor.mark_container_nodes_as_processed()
                except Exception:
                    container_count = 0
            else:
                container_count = 0

            # Ensure the processor's graph knows about these stopping nodes
            # so that successor-readiness checks treat weight ContainerNodes
            # differently (they will not call successors during newly-processed iteration).
            target_graph = processor.graph
            if not hasattr(target_graph, 'stopping_nodes') or not target_graph.stopping_nodes:
                target_graph.stopping_nodes = list(self.stopping_nodes)
                if processor.verbose:
                    print(f"Copied {len(self.stopping_nodes)} stopping_nodes into processor.graph")
        except Exception:
            # If processor.graph is unavailable for some reason, skip silently
            container_count = len(self.stopping_nodes)

        return (source_count, container_count)

    def _CreateInputLayer(self):
        """Create input layer with DataStreamNodes (streams through data automatically)."""
        from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
        
        # initialDelay=0, streamDelay=0 for ForwardProcessing (no synchronization needed)
        self.inputLayer = [DataStreamNode(name=f"x{i}", initialDelay=0, streamDelay=0) 
                          for i in range(self.numInputs)]
        for inputNode in self.inputLayer:
            self.AddNode(inputNode)

    def _CreateHiddenLayers(self):
        """Create hidden layers WITHOUT buffers."""
        for layerNum, numNeurons in enumerate(self.hiddenLayerSizes):
            hiddenLayer = []
            for i in range(numNeurons):
                # Addition node for weighted sum
                additionNode = AdditionNode(name=f"Add_H{layerNum}N{i}")
                additionNode.forcedBatchProcessing = True
                
                # Activation node
                activationNode = self.activationFunction(name=f"Act_H{layerNum}N{i}")
                activationNode.AddPreNode(additionNode)
                
                # NO BUFFER NODE - immediate propagation!
                hiddenLayer.append((additionNode, activationNode))
                self.AddNode(additionNode, activationNode)
            
            self.hiddenLayers.append(hiddenLayer)

    def _CreateOutputLayer(self):
        """Create output layer WITHOUT buffers."""
        for i in range(self.numOutputs):
            additionNode = AdditionNode(name=f"Add_y{i}")
            additionNode.forcedBatchProcessing = True
            activationNode = self.outputLayerFunction(name=f"y{i}")
            activationNode.AddPreNode(additionNode)
            
            self.outputLayer.append((additionNode, activationNode))
            self.AddNode(additionNode, activationNode)

    def _CreateWeightLayers(self):
        """Initialize weight layers with random weights between -1 and 1."""
        def random_weight():
            return random.uniform(-1, 1)

        # Input to first hidden layer
        firstHiddenLayerSize = self.hiddenLayerSizes[0]
        weightLayer = [[ContainerNode(name=f"W_x{i}H0N{j}", value=random_weight())
                        for j in range(firstHiddenLayerSize)]
                       for i in range(self.numInputs)]
        self.weightLayers.append(weightLayer)
        for row in weightLayer:
            for weightNode in row:
                self.AddNode(weightNode)
                # Treat weights as stopping nodes (suppress successors when processed)
                self.stopping_nodes.append(weightNode)

        # Between hidden layers
        for layerNum in range(self.numHiddenLayers - 1):
            weightLayer = [[ContainerNode(name=f"W_H{layerNum}N{i}H{layerNum+1}N{j}", 
                                         value=random_weight())
                            for j in range(self.hiddenLayerSizes[layerNum + 1])]
                           for i in range(self.hiddenLayerSizes[layerNum])]
            self.weightLayers.append(weightLayer)
            for row in weightLayer:
                for weightNode in row:
                    self.AddNode(weightNode)
                    self.stopping_nodes.append(weightNode)

        # Last hidden layer to output
        lastHiddenLayerSize = self.hiddenLayerSizes[-1]
        weightLayer = [[ContainerNode(name=f"W_H{self.numHiddenLayers - 1}N{i}y{j}", 
                                     value=random_weight())
                        for j in range(self.numOutputs)]
                       for i in range(lastHiddenLayerSize)]
        self.weightLayers.append(weightLayer)
        for row in weightLayer:
            for weightNode in row:
                self.AddNode(weightNode)
                self.stopping_nodes.append(weightNode)

    def _CreateLabelLayer(self):
        """Create label layer with DataStreamNodes (streams through labels automatically)."""
        from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
        
        # initialDelay=0, streamDelay=0 for ForwardProcessing (no synchronization needed)
        self.labelLayer = [DataStreamNode(name=f"Label_y{i}", initialDelay=0, streamDelay=0) 
                          for i in range(self.numOutputs)]
        for labelNode in self.labelLayer:
            self.AddNode(labelNode)

    def _CreateErrorLayer(self):
        """Create error layer (output - label)."""
        for i in range(self.numOutputs):
            errorNode = SubtractionNode(name=f"Error_y{i}")
            errorNode.AddPreNode(self.outputLayer[i][1])  # Output activation
            errorNode.AddPreNode(self.labelLayer[i])      # Label
            self.errorLayer.append(errorNode)
            self.AddNode(errorNode)

    def CreateErrorBuffers(self, bufferSize, allowNone=True):
        """
        Create BufferNode objects that record the error values over time for each
        error node in `self.errorLayer`.

        Args:
            bufferSize: Number of entries to reserve in each buffer (iterations).
            allowNone: Passed to BufferNode to permit None values if desired.

        Returns:
            List[BufferNode]: The created buffer nodes (also stored in `self.errorBuffers`).
        """
        from ComputationalGraphs.Nodes.BufferNode import BufferNode

        self.errorBuffers = []
        for i, err_node in enumerate(self.errorLayer):
            buf = BufferNode(name=f"errorBuffer{i}", size=bufferSize, allowNone=allowNone)
            buf.AddPreNode(err_node)
            self.errorBuffers.append(buf)
            self.AddNode(buf)

        return self.errorBuffers

    def _ConnectInputLayer(self):
        """Connect input layer to first hidden layer through weights."""
        self.firstLayerMultNodes = []  # Store first layer multiplication nodes
        
        for i, inputNode in enumerate(self.inputLayer):
            for j in range(self.hiddenLayerSizes[0]):
                # Create multiplication node for input * weight
                multiplicationNode = MultiplicationNode(name=f"Mult_x{i}H0N{j}")
                multiplicationNode.AddPreNode(inputNode)
                multiplicationNode.AddPreNode(self.weightLayers[0][i][j])
                
                # Connect to addition node of first hidden layer
                self.hiddenLayers[0][j][0].AddPreNode(multiplicationNode)
                self.AddNode(multiplicationNode)
                
                # Store as potential starting node
                self.firstLayerMultNodes.append(multiplicationNode)

    def _ConnectHiddenLayers(self):
        """Connect hidden layers through weights."""
        for layerNum in range(len(self.hiddenLayers) - 1):
            currentLayer = self.hiddenLayers[layerNum]
            nextLayer = self.hiddenLayers[layerNum + 1]
            weightLayer = self.weightLayers[layerNum + 1]

            for i, (_, currentActivation) in enumerate(currentLayer):
                for j in range(len(nextLayer)):
                    # Create multiplication node
                    multiplicationNode = MultiplicationNode(
                        name=f"Mult_H{layerNum}N{i}H{layerNum+1}N{j}")
                    multiplicationNode.AddPreNode(currentActivation)
                    multiplicationNode.AddPreNode(weightLayer[i][j])
                    
                    # Connect to next layer's addition node
                    nextLayer[j][0].AddPreNode(multiplicationNode)
                    self.AddNode(multiplicationNode)

    def _ConnectOutputLayer(self):
        """Connect last hidden layer to output layer through weights."""
        lastHiddenLayer = self.hiddenLayers[-1]
        weightLayer = self.weightLayers[-1]

        for i, (_, hiddenActivation) in enumerate(lastHiddenLayer):
            for j in range(self.numOutputs):
                # Create multiplication node
                multiplicationNode = MultiplicationNode(
                    name=f"Mult_H{self.numHiddenLayers-1}N{i}y{j}")
                multiplicationNode.AddPreNode(hiddenActivation)
                multiplicationNode.AddPreNode(weightLayer[i][j])
                
                # Connect to output layer's addition node
                self.outputLayer[j][0].AddPreNode(multiplicationNode)
                self.AddNode(multiplicationNode)

    def GetOutputValues(self):
        """Get current output values."""
        return [output[1].value for output in self.outputLayer]

    def GetErrorValues(self):
        """Get current error values."""
        return [error.value for error in self.errorLayer]

    def GetMSE(self):
        """Calculate Mean Squared Error."""
        errors = self.GetErrorValues()
        return sum(e**2 for e in errors) / len(errors)

    def GetRequiredIterations(self):
        """
        Calculate the number of iterations required for one complete forward pass.
        
        This is an estimate based on network depth:
        - Input layer: 1 iteration
        - Each hidden layer: 1 iteration
        - Output layer: 1 iteration
        - Total for forward pass: num_layers + 1
        
        Returns:
            int: Estimated number of iterations for complete forward pass
        """
        # Forward pass depth
        forward_depth = len(self.hiddenLayers) + 2  # inputs + hidden layers + output
        return forward_depth
    
    def GetRequiredIterationsWithBackprop(self):
        """
        Calculate the number of iterations required for one complete 
        forward+backward pass (training iteration).
        
        Includes:
        - Forward pass: ~(num_layers + 1) iterations
        - Error calculation: 1 iteration
        - Gradient computation: ~num_layers iterations (backward through network)
        - Weight updates: 1 iteration
        
        Returns:
            int: Estimated number of iterations for complete forward+backward pass
        """
        # Forward pass
        forward_depth = len(self.hiddenLayers) + 2  # inputs + hidden layers + output
        
        # Backward pass
        error_calc = 1
        gradient_depth = len(self.hiddenLayers) + 1  # gradients for each layer
        weight_update = 1
        
        total = forward_depth + error_calc + gradient_depth + weight_update
        
        return total
    
    def GetPassLength(self):
        """
        Get the length of one complete training pass (alias for GetRequiredIterationsWithBackprop).
        This is the reactivation interval for input/label nodes in cyclic training.
        
        Returns:
            int: Number of iterations per training pass (reactivation interval)
        """
        return self.GetRequiredIterationsWithBackprop()
    
    def ResetNetwork(self):
        """Reset all node values except weights."""
        for node in self.nodes:
            # Skip weight nodes
            if 'W_' not in node.name:
                node.value = 0.0
                node.inputs = []
                node.midCalculation = False
