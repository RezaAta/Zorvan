from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.SequencerNode import SequencerNode

dynamicBufferNode = SequencerNode("Dynamic Buffer")
datastreamNode1 = DataStreamNode(name = "data 1", data = [1,2,3,4,5])
datastreamNode2 = DataStreamNode(name = "data 2", data = [1,2,3,4,5])
datastreamNode3 = DataStreamNode(name = "data 3", data = [1,2,3,4,5])

dynamicBufferNode.AddPreNode(datastreamNode1,datastreamNode2,datastreamNode3)


graph = Graph()
graph.AddNode(dynamicBufferNode, datastreamNode1, datastreamNode2, datastreamNode3 )


graphProcessor = GraphProcessor(graph=graph)
graphProcessor.ComputeGraph(10)
graph.UpdateAdjacencyMatrix()
graph.DisplayGraph()