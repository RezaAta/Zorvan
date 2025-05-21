from ComputationalGraphs.Nodes.SigmoidDerivativeNode import SigmoidDerivativeNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor

sigDer = SigmoidDerivativeNode("sigmoid derviative")
dataStream = DataStreamNode("Data Stream", data= [0.5,0.52,0.53,0.54])

sigDer.AddPreNode(dataStream)

graph = Graph()
graph.AddNode(sigDer,dataStream)
graph.UpdateAdjacencyMatrix()

graphProcessor = GraphProcessor(graph,16,True) 
graphProcessor.ComputeGraph(5)
graph.DisplayGraph()