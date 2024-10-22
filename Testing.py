from Node import Node
from Graph import Graph
from AdditionNode import AdditionNode
from MultiplicationNode import MultiplicationNode
from GraphProcessor import GraphProcessor
from AbstractNode import AbstractNode

# Example setup
graph = Graph()

n1 = AdditionNode(id="A", value=10)
n2 = AdditionNode(id="B", value=20)
n3 = AdditionNode(id="C", value=30)

graph.AddNode(n1,n2,n3)

abstractNode = graph.AbstractNodes([n1,n2,n3])

        
print(graph.adjacencyMatrix)

# Initialize processor with parallel execution
processor = GraphProcessor(graph, max_workers=4)
processor.ComputeGraph(iterations=5)