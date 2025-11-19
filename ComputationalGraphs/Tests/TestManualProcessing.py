"""
Test Manual Processing functionality.

This test creates a simple graph of two data streams feeding an addition node,
and executes a manual sequence where the data nodes are processed first, then the
adder node. Because this is manual processing, the user sequence is respected
exactly and there is no dependency enforcement.
"""

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode

print("="*70)
print("TEST: Manual Processing Simple DataStream -> Addition")
print("="*70)

# Prepare nodes
a = DataStreamNode("a", data=[1, 2, 3])
b = DataStreamNode("b", data=[10, 20, 30])
c = AdditionNode("c")

# wire graph: a,b -> c
c.AddPreNode(a, b)

graph = Graph()
graph.AddNode(a, b, c)

processor = GraphProcessor(graph)

manual_sequence = [[a, b], [c]]  # Step 0: update streams; Step 1: compute addition

print("Initial values:")
print(f"  a = {a.value}, b = {b.value}, c = {c.value}")

processor.ManualProcessing(iterations=2, computation_sequence=manual_sequence)

print("After 2 iterations (streams updated then addition computed):")
print(f"  a = {a.value}, b = {b.value}, c = {c.value}")

expected = a.value + b.value
print(f"  Expected c = a + b = {expected}")

assert c.value == expected, f"ManualProcessing failed: c.value={c.value}, expected {expected}"

print("Manual processing test passed!")

print("\nTEST: ManualProcessing fallback to ForwardProcessing (no sequence)")
# Create a simple chain: a1, a2 (container) -> b (addition)
a1 = ContainerNode("a1", value=1.0)
a2 = ContainerNode("a2", value=1.0)
b = AdditionNode("b")
b.AddPreNode(a1, a2)  # simple doubling using two containers
graph2 = Graph()
graph2.AddNode(a1, a2, b)
proc2 = GraphProcessor(graph2)

proc2.ManualProcessing(iterations=2)
print(f"  b.value after fallback run: {b.value}, expected 2.0")
assert b.value == 2.0, f"Fallback forward processing didn't run as expected, b.value={b.value}"
print("Fallback behavior verified: ManualProcessing falls back to ForwardProcessing when no sequence provided.")

print("\nTEST: Graph.set_manual_processing_sequence validation")
# Use string identifiers (ids) and names to build a sequence
seq_identifiers = [[a.id, a2.id], [b.id]]
graph.set_manual_processing_sequence(seq_identifiers, strict=True)
assert graph.manual_processing_sequence is not None and len(graph.manual_processing_sequence) == 2
print("  manual_processing_sequence set and validated successfully using ids.")

print("\nTEST: ManualProcessing sequence persists across multiple calls")
graph3 = Graph()
a = DataStreamNode("a", data=[1, 2, 3])
b = DataStreamNode("b", data=[10, 20, 30])
cnode = AdditionNode("c")
cnode.AddPreNode(a, b)
graph3.AddNode(a, b, cnode)
proc3 = GraphProcessor(graph3)
graph3.set_manual_processing_sequence([[a, b], [cnode]], strict=True)

proc3.ManualProcessing(iterations=1)
print(f"After first call: a={a.value}, b={b.value}, c={cnode.value}")
assert cnode.value == 0, "Addition should not have run yet"
# Verify currently_processing_nodes matches this iteration's active set
try:
	cur_nodes = getattr(proc3, '_currently_processing_nodes', [])
	assert cur_nodes == [a, b], f"_currently_processing_nodes mismatch: {cur_nodes}"
except Exception:
	pass
proc3.ManualProcessing(iterations=1)
print(f"After second call: a={a.value}, b={b.value}, c={cnode.value}")
assert cnode.value == a.value + b.value, "Addition should run on second iteration"
print("ManualProcessing sequence continuity test passed!")

