"""
Minimal test for SubtractionNode behavior
"""

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
from ComputationalGraphs.Nodes.SubtractionNode import SubtractionNode

# Create simple graph: a - b
print("=" * 70)
print("Testing SubtractionNode: a - b")
print("=" * 70)

a_node = ContainerNode(name="a", value=10.0)
b_node = ContainerNode(name="b", value=3.0)

sub_node = SubtractionNode(name="result")
sub_node.AddPreNode(a_node)
sub_node.AddPreNode(b_node)

graph = Graph()
graph.AddNode(a_node, b_node, sub_node)

processor = GraphProcessor(graph, verbose=False)
processor.ForwardProcessing(iterations=1)

print(f"\na = {a_node.value}")
print(f"b = {b_node.value}")
print(f"result = {sub_node.value}")
print(f"Expected (a - b) = {10.0 - 3.0}")

print(f"\nPredecessors of result: {[n.name for n in sub_node.predecessors]}")
print(f"Predecessor values: {[n.value for n in sub_node.predecessors]}")

# Check if it computes a - b or b - a
if sub_node.value == 7.0:
    print("\n✓ SubtractionNode correctly computes first - second (a - b)")
elif sub_node.value == -7.0:
    print("\n✗ BUG: SubtractionNode computes second - first (b - a)")
else:
    print(f"\n✗ UNEXPECTED: SubtractionNode computed {sub_node.value}")
