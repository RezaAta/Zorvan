from Node import Node
from Graph import Graph
from AdditionNode import AdditionNode
from MultiplicationNode import MultiplicationNode
from GraphProcessor import GraphProcessor
from AbstractNode import AbstractNode
from DisplayNode import DisplayNode

# Example setup
graph = Graph()

n1 = DisplayNode(value = 10)
n2 = DisplayNode(value = 20)
n3 = DisplayNode(value = 30)
n4 = AdditionNode(value = 0)

graph.AddNode(n1,n2,n3,n4)
graph.ConnectPreNode(n4,n1,n2,n3)

abstractNode = graph.AbstractNodes([n1,n2,n3])

#compressedNode = graph.CompressNodes([n1,n2,n3])

# Initialize processor with parallel execution
processor = GraphProcessor(graph, max_workers = 4)
processor.ComputeGraph(iterations = 5)