from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.DataStreamNode import DataStreamNode

dataStreamNode = DataStreamNode("dataStream", [4, 2, 3], initialDelay=5)

graph = Graph()
graph.AddNode(dataStreamNode)

graphProcessor = GraphProcessor(graph=graph)
graphProcessor.ComputeGraph(7)
