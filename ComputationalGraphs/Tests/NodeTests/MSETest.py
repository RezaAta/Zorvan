from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.MeanSquaredNode import MeanSquaredNode

datastreamNode = DataStreamNode(name="a", data=[2, 3, 4, 5, 6])
datastreamNode2 = DataStreamNode(name="b", data=[0, 1, 2, 3, 4])
bufferNode = MeanSquaredNode(name="MS")

bufferNode.AddPreNode(datastreamNode, datastreamNode2)

graph = Graph()
graph.AddNode(bufferNode, datastreamNode, datastreamNode2)


graphProcessor = GraphProcessor(graph=graph)
graphProcessor.ComputeGraph(10)
graph.UpdateAdjacencyMatrix()
graph.DisplayGraph()
