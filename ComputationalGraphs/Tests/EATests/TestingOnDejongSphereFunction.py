from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.CrossoverNode import CrossoverNode
from ComputationalGraphs.Nodes.ExtractListElement import ExtractListElement
from ComputationalGraphs.Nodes.MutationNode import MutaionNode
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.DeJongSphereNode import DeJongSphereNode
from ComputationalGraphs.Nodes.TournamentSelectionNode import TournamentSelectionNode
from ComputationalGraphs.Nodes.SequencerNode import SequencerNode
from ComputationalGraphs.Nodes.SingleInputCrossover import SingleInputCrossover
from ComputationalGraphs.Nodes.BulkTournamentNode import BulkTournamentNode

import random

pop_size = 10
genome_length = 5

def create_population(pop_size, genome_length, lower=-5.12, upper=5.12):
    return [[random.uniform(lower, upper) for _ in range(genome_length)] for _ in range(pop_size)]

population = create_population(pop_size, genome_length)

# populationNode = SequencerNode(name = "Population", data = population)
populationNode = BufferNode(name = "Population", data = population, size = pop_size)

populationBuffer = BufferNode("Population Buffer",size = 1)
populationBuffer.AddPreNode(populationNode)

deJongNode = DeJongSphereNode("Fitness Evaluation")
deJongNode.AddPreNode(populationNode)


# tournamentNode = TournamentSelectionNode("Tournament Selection", tournamentSize = 3)
# tournamentNode.AddPreNode(populationBuffer)
# tournamentNode.AddPreNode(deJongNode)

tournamentNode = BulkTournamentNode("Tournament Selection", tournamentSize = 3, populationSize = pop_size)
tournamentNode.AddPreNode(populationBuffer)
tournamentNode.AddPreNode(deJongNode)

# populationNode.AddPreNode(tournamentNode)


crossover = SingleInputCrossover(name= "Crossover", delay=0)
crossover.AddPreNode(tournamentNode)


firstChild = ExtractListElement("First Child", 0)
firstChild.AddPreNode(crossover)

secondChild = ExtractListElement("Second Child", 1)
secondChild.AddPreNode(crossover)

crossoverPopulation = SequencerNode("Crossover Population", None)
crossoverPopulation.AddPreNode(firstChild,secondChild)

mutationNode = MutaionNode("Mutation")
mutationNode.AddPreNode(crossoverPopulation)

populationNode.AddPreNode(mutationNode)


graph = Graph()
graph.AddNode(populationNode, populationBuffer, deJongNode, tournamentNode, 
              crossover, firstChild, secondChild, crossoverPopulation, mutationNode)

#Number of iterations in each cycle of the graph can be calculated as below:
# pop_size (for population Buffer) + 1 (For fitness Evaluation) + pop_size (for tournament Node) + 5 (for crossover, mutation and assignment to population)

graphLength = pop_size + 1 + pop_size + 5

graphProcessor = GraphProcessor(graph=graph)
graphProcessor.verbose = False
graphProcessor.ComputeGraph(graphLength)


print(len(tournamentNode.population))
print(tournamentNode.populationSize)
print(len(tournamentNode.selected))

graph.UpdateAdjacencyMatrix()
graph.DisplayGraph()
