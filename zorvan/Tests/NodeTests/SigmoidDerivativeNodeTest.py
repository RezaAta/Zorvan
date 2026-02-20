from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.DataStreamNode import DataStreamNode
from zorvan.Nodes.SigmoidDerivativeNode import SigmoidDerivativeNode

sigDer = SigmoidDerivativeNode("sigmoid derviative")
dataStream = DataStreamNode("Data Stream", data=[0.5, 0.52, 0.53, 0.54])

sigDer.AddPreNode(dataStream)

graph = Graph()
graph.AddNode(sigDer, dataStream)
graph.UpdateAdjacencyMatrix()

graphProcessor = GraphProcessor(graph, 16, True)
graphProcessor.ComputeGraph(5)
graph.DisplayGraph()
