from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.SubtractionNode import SubtractionNode


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
