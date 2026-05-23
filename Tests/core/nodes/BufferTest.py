from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.AdditionNode import AdditionNode
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.DataStreamNode import DataStreamNode
from zorvan.Nodes.DisplayNode import DisplayNode

datastreamNode = DataStreamNode(name="data", data=[1, 2, 3, 4, 5])
bufferNode = BufferNode(name="buffer", size=1)
displayNode = DisplayNode(name="a")
additionNode = AdditionNode(name="sum")

bufferNode.AddPreNode(datastreamNode)
additionNode.AddPreNode(bufferNode, displayNode)
displayNode.AddPreNode(datastreamNode)

graph = Graph()
graph.AddNode(bufferNode, datastreamNode, displayNode, additionNode)


graphProcessor = GraphProcessor(graph=graph)
graphProcessor.ComputeGraph(10)
graph.UpdateAdjacencyMatrix()
graph.DisplayGraph()
