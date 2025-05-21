from ComputationalGraphs.Core.BufferNode import BufferNode
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode

datastreamNode = DataStreamNode(name = "data", data = [1,2,3,4,5])
bufferNode = BufferNode(name = "buffer",size=1)
displayNode = DisplayNode(name = "a")
additionNode = AdditionNode(name= "sum")

bufferNode.AddPreNode(datastreamNode)
additionNode.AddPreNode(bufferNode, displayNode)
displayNode.AddPreNode(datastreamNode)

graph = Graph()
graph.AddNode(bufferNode, datastreamNode, displayNode,additionNode)


graphProcessor = GraphProcessor(graph=graph)
graphProcessor.ComputeGraph(10)
graph.UpdateAdjacencyMatrix()
graph.DisplayGraph()