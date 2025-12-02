"""
Test Forward Processing functionality.

Tests the forward processing algorithm with different graph structures.
Active nodes (whose predecessors have completed) are processed in each iteration.
"""

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode

print("=" * 70)
print("TEST 1: Simple Linear Chain (a → b → c → d)")
print("=" * 70)

# Create nodes
a = ContainerNode("a", value=1.0)
b = AdditionNode("b")
c = MultiplicationNode("c")
d = AdditionNode("d")

# Create connections: a → b → c → d
b.AddPreNode(a)
c.AddPreNode(b)
d.AddPreNode(c)

# Build graph
graph1 = Graph()
graph1.AddNode(a, b, c, d)

# Process - execute until completion
processor1 = GraphProcessor(graph1, verbose=True)
iterations = processor1.ForwardProcessingComplete()

print(f"\nTotal iterations executed: {iterations}")
print("Expected execution order:")
print("  Iteration 0: [a]")
print("  Iteration 1: [b]")
print("  Iteration 2: [c]")
print("  Iteration 3: [d]")

print("\n" + "=" * 70)
print("TEST 2: Diamond Graph (a → b → d, a → c → d)")
print("=" * 70)

# Create nodes
a2 = ContainerNode("a", value=2.0)
b2 = AdditionNode("b")
c2 = MultiplicationNode("c")
d2 = AdditionNode("d")

# Create connections: a → b → d, a → c → d
b2.AddPreNode(a2)
c2.AddPreNode(a2)
d2.AddPreNode(b2, c2)

# Build graph
graph2 = Graph()
graph2.AddNode(a2, b2, c2, d2)

# Process - execute until completion
processor2 = GraphProcessor(graph2, verbose=True)
iterations = processor2.ForwardProcessingComplete()

print(f"\nTotal iterations executed: {iterations}")
print("Expected execution order:")
print("  Iteration 0: [a]")
print("  Iteration 1: [b, c]")
print("  Iteration 2: [d]")

print("\n" + "=" * 70)
print("TEST 3: Complex Multi-Branch")
print("=" * 70)

# Create nodes
a3 = ContainerNode("a", value=1.0)
b3 = ContainerNode("b", value=2.0)
c3 = AdditionNode("c")
d3 = MultiplicationNode("d")
e3 = AdditionNode("e")
f3 = AdditionNode("f")

# Connections:
# a → c → e → f
# b → d → e → f
c3.AddPreNode(a3)
d3.AddPreNode(b3)
e3.AddPreNode(c3, d3)
f3.AddPreNode(e3)

# Build graph
graph3 = Graph()
graph3.AddNode(a3, b3, c3, d3, e3, f3)

# Process - execute until completion
processor3 = GraphProcessor(graph3, verbose=True)
iterations = processor3.ForwardProcessingComplete()

print(f"\nTotal iterations executed: {iterations}")
print("Expected execution order:")
print("  Iteration 0: [a, b]")
print("  Iteration 1: [c, d]")
print("  Iteration 2: [e]")
print("  Iteration 3: [f]")

print("\n" + "=" * 70)
print("TEST 4: Multiple Iterations (Simulating Training)")
print("=" * 70)

# Create simple network
input_node = ContainerNode("input", value=1.0)
hidden_node = AdditionNode("hidden")
output_node = MultiplicationNode("output")

hidden_node.AddPreNode(input_node)
output_node.AddPreNode(hidden_node)

# Build graph
graph4 = Graph()
graph4.AddNode(input_node, hidden_node, output_node)

# Process multiple iterations
processor4 = GraphProcessor(graph4, verbose=False)

print("Running 3 passes with different input values:")
for i in range(3):
    input_node.value = float(i + 1)
    print(f"\nPass {i+1}: input = {input_node.value}")

    # Reset state and process complete pass
    processor4.reset_forward_state()
    iterations = processor4.ForwardProcessingComplete()

    print(f"  Iterations: {iterations}")
    print(f"  hidden = {hidden_node.value}")
    print(f"  output = {output_node.value}")

print("\n" + "=" * 70)
print("All tests completed!")
print("=" * 70)
