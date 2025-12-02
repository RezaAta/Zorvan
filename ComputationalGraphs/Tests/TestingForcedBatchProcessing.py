from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode

node1 = DisplayNode("a", value=1)
node2 = DisplayNode("b", value=2)
node3 = DisplayNode("c", value=3)

additionNode = AdditionNode("sum", value=0)
additionNode.forcedBatchProcessing = True
additionNode.AddPreNode(node1, node2, node3)

graph = Graph()
graph.AddNode(node1, node2, node3, additionNode)

graphProcessor = GraphProcessor(graph=graph)
graphProcessor.ComputeGraph(10)

additionNode.forcedBatchProcessing = False
# graphProcessor.ComputeGraph(10)
