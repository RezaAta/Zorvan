from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.CrossoverNode import CrossoverNode
from ComputationalGraphs.Nodes.ExtractListElement import ExtractListElement
from ComputationalGraphs.Nodes.MutationNode import MutaionNode
from ComputationalGraphs.Nodes.BufferNode import BufferNode

populationNode = DataStreamNode(name = "population", data = [[1,2],[2,3],[3,4],[4,5],[5,6]])

displayNode = DisplayNode(name = "a")
crossover = CrossoverNode(name= "Crossover")

firstChild = ExtractListElement("First Child", 0)
firstChild.AddPreNode(crossover)

secondChild = ExtractListElement("Second Child", 1)
secondChild.AddPreNode(crossover)

crossoverPopulation = BufferNode("Crossover Population", None, 5)
crossoverPopulation.AddPreNode(firstChild,secondChild)

mutationNode = MutaionNode("Mutation")
mutationNode.AddPreNode(crossoverPopulation)



crossover.AddPreNode(displayNode, populationNode)
displayNode.AddPreNode(populationNode)

graph = Graph()
graph.AddNode(populationNode, displayNode, crossover, firstChild, secondChild, crossoverPopulation, mutationNode)


graphProcessor = GraphProcessor(graph=graph)
graphProcessor.ComputeGraph(20)
graph.UpdateAdjacencyMatrix()
graph.DisplayGraph()
print(crossoverPopulation.buffer)