from Node import Node
from Graph import Graph
from AdditionNode import AdditionNode
from DisplayNode import DisplayNode
from GraphProcessor import GraphProcessor


# Example setup
graph = Graph()

fib1 = DisplayNode(name="Fibonacci n-1", value=1)
fibn = AdditionNode(name="Fibonacci n", value=1)

graph.AddNode(fib1, fibn)

graph.ConnectPreNode(fibn, fibn, fib1)
graph.ConnectPreNode(fib1, fibn)



# Initialize processor with parallel execution
processor = GraphProcessor(graph, max_workers=4)
processor.ComputeGraph(iterations=500)