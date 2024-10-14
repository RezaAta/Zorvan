from platform import node
from ComputationalGraphs.Graph import Graph
from ComputationalGraphs.AdditionNode import AdditionNode

node1 = AdditionNode("a")
node2 = AdditionNode("b",value = 5)
node3 = AdditionNode("c",value = 3)
                     
node1.add_pre_node(node2)
node1.add_pre_node(node3)

print(node1.predecessors)

result = node1.operation()

print(f"Result: {result}")


graph = Graph();

graph.AddNode(node1)
graph.AddNode(node2)
graph.AddNode(node3)
print(graph)

graph.update_adjacency_matrix()
print(graph.adjacencyMatrix)
