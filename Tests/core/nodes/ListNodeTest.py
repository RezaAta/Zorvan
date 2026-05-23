from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.DataStreamNode import DataStreamNode
from zorvan.Nodes.ListNode import ListNode

datastreamNode1 = DataStreamNode(name="data1", data=[1, 2, None, 4, 5])
datastreamNode2 = DataStreamNode(name="data2", data=[1, 2, 3, 4, 5])

listNode = ListNode(name="list", allowNone=False)
listNode.AddPreNode(datastreamNode1, datastreamNode2)

bufferNode = BufferNode(name="buffer", size=3)
bufferNode.AddPreNode(listNode)


bufferNode2 = BufferNode(name="buffer2", size=3)
bufferNode2.AddPreNode(datastreamNode1)


graph = Graph()
graph.AddNode(bufferNode, bufferNode2, datastreamNode1, datastreamNode2, listNode)
graph.UpdateAdjacencyMatrix()


graphProcessor = GraphProcessor(graph=graph)

graphProcessor.ComputeGraphSingleThread(10)
print(bufferNode.buffer)
print(bufferNode2.buffer)
