from Graph import Graph
from DisplayNode import DisplayNode
from AdditionNode import AdditionNode
from MultiplicationNode import MultiplicationNode
from SigmoidNode import SigmoidNode
from graphviz import Digraph

class MLPGraph(Graph):
    def __init__(self, numInputs, numOutputs, numLayers, learningRate, activationFunction=SigmoidNode):
        super().__init__()
        self.numInputs = numInputs
        self.numOutputs = numOutputs
        self.numLayers = numLayers
        self.learningRate = learningRate
        self.activationFunction = activationFunction
        
        self.inputLayer = []
        self.outputLayer = []
        self.hiddenLayers = []
        self.weightLayers = []  # Separate layers for weights to facilitate weight management

    def BuildMLP(self):
        """Build the MLP architecture by initializing and connecting layers."""
        self._create_input_layer()
        self._create_hidden_layers()
        self._create_output_layer()
        self._create_weight_layers()  # Create all weight layers after other layers are initialized
        
        # Connect layers in sequence
        self._connect_input_layer()
        self._connect_hidden_layers()
        self._connect_output_layer()

    def _create_input_layer(self):
        """Initialize the input layer with DisplayNodes for each input."""
        self.inputLayer = [DisplayNode(name=f"Input_{i}") for i in range(self.numInputs)]
        for node in self.inputLayer:
            self.AddNode(node)

    def _create_hidden_layers(self):
        """Initialize hidden layers with addition and activation nodes."""
        for layerNum in range(self.numLayers):
            hiddenLayer = []
            for i in range(self.numInputs):
                additionNode = AdditionNode(name=f"Addition_L{layerNum}_N{i}")
                activationNode = self.activationFunction(name=f"Activation_L{layerNum}_N{i}")
                activationNode.AddPreNode(additionNode)
                hiddenLayer.append((additionNode, activationNode))
                self.AddNode(additionNode, activationNode)
            self.hiddenLayers.append(hiddenLayer)

    def _create_weight_layers(self):
        """Initialize weight layers to connect each subsequent layer pair."""
        # First weight layer connects input to the first hidden layer
        weightLayer = [[DisplayNode(name=f"Weight_Input{i}_to_Hidden0_{j}", value=1.0)
                        for j in range(self.numInputs)]
                       for i in range(self.numInputs)]
        self.weightLayers.append(weightLayer)
        for row in weightLayer:
            for weightNode in row:
                self.AddNode(weightNode)

        # Weight layers between hidden layers
        for layerNum in range(self.numLayers - 1):
            weightLayer = [[DisplayNode(name=f"Weight_Hidden{layerNum}_N{i}_to_Hidden{layerNum+1}_N{j}", value=1.0)
                            for j in range(self.numInputs)]
                           for i in range(self.numInputs)]
            self.weightLayers.append(weightLayer)
            for row in weightLayer:
                for weightNode in row:
                    self.AddNode(weightNode)

        # Last weight layer connects the last hidden layer to the output layer
        weightLayer = [[DisplayNode(name=f"Weight_Hidden{self.numLayers-1}_N{i}_to_Output{j}", value=1.0)
                        for j in range(self.numOutputs)]
                       for i in range(self.numInputs)]
        self.weightLayers.append(weightLayer)
        for row in weightLayer:
            for weightNode in row:
                self.AddNode(weightNode)

    def _create_output_layer(self):
        """Initialize the output layer with addition and activation nodes."""
        for i in range(self.numOutputs):
            additionNode = AdditionNode(name=f"Addition_Output_N{i}")
            activationNode = self.activationFunction(name=f"Output_Activation_N{i}")
            activationNode.AddPreNode(additionNode)
            self.outputLayer.append((additionNode, activationNode))
            self.AddNode(additionNode, activationNode)

    def _connect_input_layer(self):
        """Connect the input layer to the first hidden layer with weight nodes."""
        firstHiddenLayer = self.hiddenLayers[0]
        weightLayer = self.weightLayers[0]
        
        for i, inputNode in enumerate(self.inputLayer):
            for j, (nextAddNode, _) in enumerate(firstHiddenLayer):
                weightNode = weightLayer[i][j]
                multNode = MultiplicationNode(name=f"Mult_Input{i}_to_Hidden{j}")
                multNode.AddPreNode(inputNode)
                multNode.AddPreNode(weightNode)
                nextAddNode.AddPreNode(multNode)
                self.AddNode(multNode)

    def _connect_hidden_layers(self):
        """Connect each hidden layer to the next hidden layer using weight nodes."""
        for layerNum in range(self.numLayers - 1):
            prevLayer = self.hiddenLayers[layerNum]
            nextLayer = self.hiddenLayers[layerNum + 1]
            weightLayer = self.weightLayers[layerNum + 1]
            
            for i, (_, prevActNode) in enumerate(prevLayer):
                for j, (nextAddNode, _) in enumerate(nextLayer):
                    weightNode = weightLayer[i][j]
                    multNode = MultiplicationNode(name=f"Mult_Hidden{layerNum}_N{i}_to_Hidden{layerNum+1}_N{j}")
                    multNode.AddPreNode(prevActNode)
                    multNode.AddPreNode(weightNode)
                    nextAddNode.AddPreNode(multNode)
                    self.AddNode(multNode)

    def _connect_output_layer(self):
        """Connect the last hidden layer to the output layer with weight nodes."""
        lastHiddenLayer = self.hiddenLayers[-1]
        weightLayer = self.weightLayers[-1]
        
        for i, (_, lastActNode) in enumerate(lastHiddenLayer):
            for j, (outputAddNode, _) in enumerate(self.outputLayer):
                weightNode = weightLayer[i][j]
                multNode = MultiplicationNode(name=f"Mult_Hidden{self.numLayers-1}_N{i}_to_Output{j}")
                multNode.AddPreNode(lastActNode)
                multNode.AddPreNode(weightNode)
                outputAddNode.AddPreNode(multNode)
                self.AddNode(multNode)

    def DisplayGraph(self):
        """Visualize the MLP graph using Graphviz."""
        dot = Digraph(format='png')
        for node in self.nodes:
            dot.node(node.name, label=f"{node.name}\n({type(node).__name__})")
        for i, row in enumerate(self.adjacencyMatrix):
            for j, connection in enumerate(row):
                if connection == 1:
                    dot.edge(self.nodes[i].name, self.nodes[j].name)
        dot.render(filename='mlp_graph', view=True)

    def GetLayerNodes(self, layerType, layerIndex):
        """Retrieve nodes from a specified layer type and index."""
        if layerType == 'input':
            return self.inputLayer
        elif layerType == 'output':
            return self.outputLayer
        elif layerType == 'hidden' and 0 <= layerIndex < len(self.hiddenLayers):
            return self.hiddenLayers[layerIndex]
        elif layerType == 'weight' and 0 <= layerIndex < len(self.weightLayers):
            return self.weightLayers[layerIndex]
        else:
            raise ValueError("Invalid layer type or index.")
