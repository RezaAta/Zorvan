from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.CrossoverNode import CrossoverNode
from zorvan.Nodes.DataStreamNode import DataStreamNode
from zorvan.Nodes.DisplayNode import DisplayNode
from zorvan.Nodes.ExtractListElement import ExtractListElement
from zorvan.Nodes.MutationNode import MutaionNode

populationNode = DataStreamNode(
    name="population", data=[[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]]
)

displayNode = DisplayNode(name="a")
crossover = CrossoverNode(name="Crossover")

firstChild = ExtractListElement("First Child", 0)
firstChild.AddPreNode(crossover)

secondChild = ExtractListElement("Second Child", 1)
secondChild.AddPreNode(crossover)

crossoverPopulation = BufferNode("Crossover Population", None, 5)
crossoverPopulation.AddPreNode(firstChild, secondChild)

mutationNode = MutaionNode("Mutation")
mutationNode.AddPreNode(crossoverPopulation)


crossover.AddPreNode(displayNode, populationNode)
displayNode.AddPreNode(populationNode)

graph = Graph()
graph.AddNode(
    populationNode,
    displayNode,
    crossover,
    firstChild,
    secondChild,
    crossoverPopulation,
    mutationNode,
)


graphProcessor = GraphProcessor(graph=graph)
graphProcessor.ComputeGraph(20)
graph.UpdateAdjacencyMatrix()
graph.DisplayGraph()
print(crossoverPopulation.buffer)
