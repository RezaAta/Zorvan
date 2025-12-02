from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode

dataStreamNode = DataStreamNode("dataStream", [4, 2, 3], initialDelay=5)

graph = Graph()
graph.AddNode(dataStreamNode)

graphProcessor = GraphProcessor(graph=graph)
graphProcessor.ComputeGraph(7)
