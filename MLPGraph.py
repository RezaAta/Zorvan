from Graph import Graph
from BufferNode import BufferNode
from ContainerNode import ContainerNode
from AdditionNode import AdditionNode
from MultiplicationNode import MultiplicationNode
from SigmoidNode import SigmoidNode
from DataStreamNode import DataStreamNode
from MeanSquaredErrorNode import MeanSquaredErrorNode  # Import the node for calculating error

class MLPGraph(Graph):
    def __init__(self, numInputs, numOutputs, numHiddenLayers, activationFunction=SigmoidNode, hiddenLayerSizes=None):
        super().__init__()
        self.numInputs = numInputs
        self.numOutputs = numOutputs
        self.numHiddenLayers = numHiddenLayers
        self.activationFunction = activationFunction
        self.hiddenLayerSizes = hiddenLayerSizes if hiddenLayerSizes else [numInputs] * numHiddenLayers
        
        self.inputLayer = []
        self.outputLayer = []
        self.hiddenLayers = []
        self.weightLayers = []  # Separate layers for weights to facilitate weight management
        self.labelLayer = []
        self.errorLayer = []

    def BuildMLP(self):
        """Build the MLP architecture by initializing and connecting layers."""
        self._CreateInputLayer()
        self._CreateHiddenLayers()
        self._CreateOutputLayer()
        self._CreateWeightLayers()  # Create all weight layers after other layers are initialized
        self._CreateLabelLayer()      # Add the label layer
        self._CreateErrorLayer()      # Add the error layer
        
        # Connect layers in sequence
        self._ConnectInputLayer()
        self._ConnectHiddenLayers()
        self._ConnectOutputLayer()
        self.UpdateAdjacencyMatrix()

    def LoadData(self, inputData, labelsData):
        if len(inputData) != self.numInputs:
            raise ValueError("Data size must match the number of input nodes.")

        for i, row in enumerate(inputData):
            self.inputLayer[i][0].data = row  # Assign the data list to the node's data attribute
            self.inputLayer[i][0].iteration = 0  # Reset iteration to start from the beginning
            self.inputLayer[i][0].streamIndex = 0  # Reset stream index for new data
        
        for i, row in enumerate(labelsData):
            self.labelLayer[i].data = row  # Assign the data list to the node's data attribute
            self.labelLayer[i].iteration = 0  # Reset iteration to start from the beginning
            self.labelLayer[i].streamIndex = 0  # Reset stream index for new data

    def _CreateInputLayer(self):
        """Initialize the input layer with DataStreamNode for each input."""
        self.inputLayer = [(DataStreamNode(name=f"x{i}"), BufferNode(name=f"Buff_x{i}", size=((self.numHiddenLayers + 1) * 6) - 1)) for i in range(self.numInputs)]
        for (inputNode, bufferNode) in self.inputLayer:
            bufferNode.AddPreNode(inputNode)
            self.AddNode(inputNode, bufferNode)

    def _CreateHiddenLayers(self):
        """Initialize hidden layers with addition and activation nodes."""
        for layerNum, numNeurons in enumerate(self.hiddenLayerSizes):
            hiddenLayer = []
            for i in range(numNeurons):
                additionNode = AdditionNode(name=f"Add_L{layerNum}N{i}")
                additionNode.forcedBatchProcessing = True
                activationNode = self.activationFunction(name=f"Act_L{layerNum}N{i}")
                activationNode.AddPreNode(additionNode)
                layersAhead = (self.numHiddenLayers + 2) - (layerNum + 2)
                bufferNode = BufferNode(name=f"Buff_H{layerNum}N{i}", size=(layersAhead * 6) - 1)
                bufferNode.AddPreNode(activationNode)

                hiddenLayer.append((additionNode, activationNode, bufferNode))
                self.AddNode(additionNode, activationNode, bufferNode)

            self.hiddenLayers.append(hiddenLayer)
            
    def _CreateOutputLayer(self):
        """Initialize the output layer with addition and activation nodes."""
        for i in range(self.numOutputs):
            additionNode = AdditionNode(name=f"Add_y{i}")
            additionNode.forcedBatchProcessing = True
            activationNode = self.activationFunction(name=f"y{i}")
            activationNode.AddPreNode(additionNode)
            self.outputLayer.append((additionNode, activationNode))
            self.AddNode(additionNode, activationNode)

    def _CreateWeightLayers(self):
        """Initialize weight layers to connect each subsequent layer pair."""
        # First weight layer connects input to the first hidden layer
        firstHiddenLayerSize = self.hiddenLayerSizes[0]
        weightLayer = [[ContainerNode(name=f"W_x{i}H0N{j}", value=0.5) for j in range(firstHiddenLayerSize)]
                       for i in range(self.numInputs)]
        self.weightLayers.append(weightLayer)
        for row in weightLayer:
            for weightNode in row:
                self.AddNode(weightNode)

        # Weight layers between hidden layers
        for layerNum in range(self.numHiddenLayers - 1):
            weightLayer = [[ContainerNode(name=f"W_H{layerNum}N{i}H{layerNum+1}N{j}", value=0.5)
                            for j in range(self.hiddenLayerSizes[layerNum + 1])]
                           for i in range(self.hiddenLayerSizes[layerNum])]
            self.weightLayers.append(weightLayer)
            for row in weightLayer:
                for weightNode in row:
                    self.AddNode(weightNode)

        # Last weight layer connects the last hidden layer to the output layer
        lastHiddenLayerSize = self.hiddenLayerSizes[-1]
        weightLayer = [[ContainerNode(name=f"W_H{self.numHiddenLayers - 1}N{i}y{j}", value=0.5)
                        for j in range(self.numOutputs)]
                       for i in range(lastHiddenLayerSize)]
        self.weightLayers.append(weightLayer)
        for row in weightLayer:
            for weightNode in row:
                self.AddNode(weightNode)

    def _CreateLabelLayer(self):
        """Create the label layer with DataStreamNodes for expected output values."""
        self.labelLayer = [DataStreamNode(name=f"L_y{i}", initialDelay = self.numHiddenLayers*3) for i in range(self.numOutputs)]
        for node in self.labelLayer:
            self.AddNode(node)

    def _CreateErrorLayer(self):
        """Create the error layer using MeanSquaredErrorNodes for calculating errors."""
        self.errorLayer = []
        for i, (outputAddNode, outputActNode) in enumerate(self.outputLayer):
            errorNode = MeanSquaredErrorNode(name=f"Error_y{i}")
            errorNode.AddPreNode(outputActNode)  # Connect output activation to error node
            errorNode.AddPreNode(self.labelLayer[i])  # Connect corresponding label node
            self.errorLayer.append(errorNode)
            self.AddNode(errorNode)

    def _ConnectInputLayer(self):
        """Connect the input layer to the first hidden layer with weight nodes."""
        firstHiddenLayer = self.hiddenLayers[0]
        weightLayer = self.weightLayers[0]
        
        for i, (inputNode,bufferNode) in enumerate(self.inputLayer):
            for j, (nextAddNode, nextActNode, nextBufferNode) in enumerate(firstHiddenLayer):
                weightNode = weightLayer[i][j]
                multNode = MultiplicationNode(name=f"Mul_x{i}H{j}")
                multNode.AddPreNode(inputNode)
                multNode.AddPreNode(weightNode)
                nextAddNode.AddPreNode(multNode)
                self.AddNode(multNode)

    def _ConnectHiddenLayers(self):
        """Connect each hidden layer to the next hidden layer using weight nodes."""
        for layerNum in range(self.numHiddenLayers - 1):
            prevLayer = self.hiddenLayers[layerNum]
            nextLayer = self.hiddenLayers[layerNum + 1]
            weightLayer = self.weightLayers[layerNum + 1]
            
            for i, (_, prevActNode, bufferNode) in enumerate(prevLayer):
                for j, (nextAddNode, _, bufferNode) in enumerate(nextLayer):
                    weightNode = weightLayer[i][j]
                    multNode = MultiplicationNode(name=f"Mul_H{layerNum}N{i}H{layerNum+1}N{j}")
                    multNode.AddPreNode(prevActNode)
                    multNode.AddPreNode(weightNode)
                    nextAddNode.AddPreNode(multNode)
                    self.AddNode(multNode)

    def _ConnectOutputLayer(self):
        """Connect the last hidden layer to the output layer with weight nodes."""
        lastHiddenLayer = self.hiddenLayers[-1]
        weightLayer = self.weightLayers[-1]
        
        for i, (lastAddNode, lastActNode, lastbuffNode) in enumerate(lastHiddenLayer):
            for j, (outputAddNode, outputActNode) in enumerate(self.outputLayer):
                weightNode = weightLayer[i][j]
                multNode = MultiplicationNode(name=f"Mul_H{self.numHiddenLayers-1}N{i}y{j}")
                multNode.AddPreNode(lastActNode)
                multNode.AddPreNode(weightNode)
                outputAddNode.AddPreNode(multNode)
                self.AddNode(multNode)