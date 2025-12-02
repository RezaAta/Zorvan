from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode

# Example setup
graph = Graph()

sigInput = DisplayNode(name="input", value=0.5)
sigmoid = SigmoidNode(name="Sigmoid")
sigmoid.AddPreNode(sigInput)

graph.AddNode(sigInput, sigmoid)
graph.UpdateAdjacencyMatrix()

# Initialize processor with parallel execution
processor = GraphProcessor(graph, max_workers=4)
processor.ComputeGraph(iterations=2)

graph.DisplayGraph()
