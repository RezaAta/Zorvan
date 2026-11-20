from zorvan_reference.Core.Graph import Graph
from zorvan_reference.Core.GraphProcessor import GraphProcessor
from zorvan_reference.Nodes.AdditionNode import AdditionNode
from zorvan_reference.Nodes.DisplayNode import DisplayNode


def test_forced_batch_processing_sums_all_inputs_across_batches():
    node1 = DisplayNode("a", value=1)
    node2 = DisplayNode("b", value=2)
    node3 = DisplayNode("c", value=3)

    addition_node = AdditionNode("sum")
    addition_node.forcedBatchProcessing = True
    addition_node.AddPreNode(node1, node2, node3)

    graph = Graph()
    graph.AddNode(node1, node2, node3, addition_node)
    graph.UpdateAdjacencyMatrix()

    GraphProcessor(graph, verbose=False).ComputeGraph(iterations=1)

    assert addition_node.value == 6
