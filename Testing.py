from Node import Node
from Graph import Graph
from AdditionNode import AdditionNode
from MultiplicationNode import MultiplicationNode
from GraphProcessor import GraphProcessor


# Example setup
graph = Graph()

node1 = AdditionNode(name="A", value=10)
node2 = AdditionNode(name="B", value=20)
node3 = MultiplicationNode(name="C", value=30)

graph.AddNode(node1,node2,node3)
# graph.AddNode(node2)
# graph.AddNode(node3)
# graph.ConnectPreNode(node2, node1)  # A -> B
# graph.ConnectPreNode(node3, node2)  # C -> B
# graph.ConnectPreNode(node1, node3)  # B -> C
# graph.ConnectPreNode(node1, node2)  # A -> B
# graph.ConnectPreNode(node3, node1)  # A -> B
# graph.ConnectPreNode(node2, node3)  # A -> B


# Initialize processor with parallel execution
processor = GraphProcessor(graph, max_workers=4)
processor.ComputeGraph(iterations=5)