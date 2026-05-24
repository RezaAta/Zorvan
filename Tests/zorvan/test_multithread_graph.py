from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes.AdditionNode import AdditionNode


def build_test_graph(num_nodes):
    graph = Graph()
    for i in range(num_nodes):
        graph.AddNode(AdditionNode(name=f"node{i}", value=0))
    graph.nodes[0].value = 1

    for i in range(num_nodes):
        predecessor1 = graph.nodes[i - 1]
        predecessor2 = graph.nodes[i - 2]
        graph.ConnectPreNode(graph.nodes[i], predecessor1, predecessor2)

    return graph


def get_graph_values(graph):
    return [node.value for node in graph.nodes]


def test_graph_processor_with_multiple_workers_matches_single_thread():
    graph_single = build_test_graph(16)
    graph_multi = build_test_graph(16)

    GraphProcessor(graph_single, max_workers=1, verbose=False).ComputeGraph(iterations=10)
    GraphProcessor(graph_multi, max_workers=16, verbose=False).ComputeGraph(iterations=10)

    assert get_graph_values(graph_single) == get_graph_values(graph_multi)
