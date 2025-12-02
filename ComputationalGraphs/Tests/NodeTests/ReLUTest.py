from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.ReLUDerivativeNode import ReLUDerivativeNode
from ComputationalGraphs.Nodes.ReLUNode import ReLUNode

displayNode = DisplayNode("display", value=-0.28)
reluNode = ReLUNode("ReLU")
reluDerivative = ReLUDerivativeNode("Derivative")

reluNode.AddPreNode(displayNode)
reluDerivative.AddPreNode(reluNode)

graph = Graph()
graph.AddNode(displayNode, reluNode, reluDerivative)

graphProcessor = GraphProcessor(graph, verbose=True)
graphProcessor.ComputeGraph(10)
