from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.DisplayNode import DisplayNode
from zorvan.Nodes.ReLUDerivativeNode import ReLUDerivativeNode
from zorvan.Nodes.ReLUNode import ReLUNode

displayNode = DisplayNode("display", value=-0.28)
reluNode = ReLUNode("ReLU")
reluDerivative = ReLUDerivativeNode("Derivative")

reluNode.AddPreNode(displayNode)
reluDerivative.AddPreNode(reluNode)

graph = Graph()
graph.AddNode(displayNode, reluNode, reluDerivative)

graphProcessor = GraphProcessor(graph, verbose=True)
graphProcessor.ComputeGraph(10)
