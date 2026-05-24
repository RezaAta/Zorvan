import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.AdditionNode import AdditionNode
from zorvan.Nodes.DisplayNode import DisplayNode
from zorvan.Nodes.SubtractionNode import SubtractionNode


# Example setup
def RunSimpleProfitCalculator():
    graph = Graph()

    price = DisplayNode(name="Price", value=2000)
    transition_cost = DisplayNode(name="Transition Cost", value=200)
    production_cost = DisplayNode(name="Production Cost", value=1000)

    total_cost = AdditionNode(name="Total Cost", value=0)
    total_cost.AddPreNode(transition_cost, production_cost)

    profit = SubtractionNode(name="Profit", value=0)
    # Profit should be Price - Total Cost
    profit.AddPreNode(price, total_cost)

    # Add nodes once (no duplicates) and in a clear order
    graph.AddNode(price, transition_cost, production_cost, total_cost, profit)

    # Update adjacency before running the processor
    graph.UpdateAdjacencyMatrix()

    processor = GraphProcessor(graph, max_workers=4)
    processor.ComputeGraph(iterations=10)

    graph.DisplayGraph()


if __name__ == "__main__":
    RunSimpleProfitCalculator()
