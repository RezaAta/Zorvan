"""
Manual Processing Example

This example demonstrates using ManualProcessing by setting a manual sequence
on a small graph and stepping through the sequence explicitly.
"""
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode

def manual_example():
    a = DataStreamNode("a", data=[1,2,3])
    b = DataStreamNode("b", data=[10,20,30])
    c = AdditionNode("c")
# wire
    c.AddPreNode(a,b)

    graph = Graph()
    graph.AddNode(a,b,c)

    proc = GraphProcessor(graph)

    # Basic manual sequence: step 0 -> update inputs; step 1 -> compute addition
    sequence = [[a,b], [c]]
    print("Manual sequence:", [[n.name for n in s] for s in sequence])
    for i in range(4):
        print(f"--- Iteration {i}")
        proc.ManualProcessing(iterations=1, computation_sequence=sequence)
        print(f"  a={a.value}, b={b.value}, c={c.value}")

if __name__ == '__main__':
    manual_example()
