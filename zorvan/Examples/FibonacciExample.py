import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.AdditionNode import AdditionNode
from zorvan.Nodes.DisplayNode import DisplayNode


# Example setup
def RunFibonacciFunction():
    graph = Graph()

    fib1 = DisplayNode(name="Fibonacci n-1", value=1)
    fibn = AdditionNode(name="Fibonacci n", value=1)

    graph.AddNode(fib1, fibn)

    graph.ConnectPreNode(fibn, fibn, fib1)
    graph.ConnectPreNode(fib1, fibn)

    # Initialize processor with parallel execution
    processor = GraphProcessor(graph, max_workers=4)
    processor.ComputeGraph(iterations=10)

    graph.DisplayGraph()


if __name__ == "__main__":
    RunFibonacciFunction()
