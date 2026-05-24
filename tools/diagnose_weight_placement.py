"""Diagnose weight stacking issue in MLP Layout."""

from gui_framework.legacy import MLPLayoutEngine


class MockNode:
    def __init__(self, name):
        self.name = name
        self.predecessors = []


# Test 1: Basic weight placement
print("=" * 50)
print("TEST 1: Basic weight placement with 2 weights to 1 mult")
print("=" * 50)

mult_y0 = MockNode("Mul_H0N0y0")
w0 = MockNode("W_H0N0y0")
w1 = MockNode("W_H0N1y0")
mult_y0.predecessors = [w0, w1]

nodes = [mult_y0, w0, w1]
engine = MLPLayoutEngine(nodes, grid_size=80)
engine.place_node(mult_y0, 10, 0)

print(f"W_H0N0y0 neuron number: {engine.get_neuron_number(w0)}")
print(f"W_H0N1y0 neuron number: {engine.get_neuron_number(w1)}")

engine._place_weights_for_mults([mult_y0], 10)

print(f"W_H0N0y0 grid: {engine.get_grid_coords(w0)}")
print(f"W_H0N1y0 grid: {engine.get_grid_coords(w1)}")
print(
    f"Different positions? {engine.get_grid_coords(w0) != engine.get_grid_coords(w1)}"
)

# Test 2: Multiple mults each with their own weight
print("\n" + "=" * 50)
print("TEST 2: Multiple output mults, each with multiple weights")
print("=" * 50)

# Simulate: 2 hidden neurons -> 1 output
# Mul_H0N0y0 gets inputs from Act_H0N0 * W_H0N0y0
# Mul_H0N1y0 gets inputs from Act_H0N1 * W_H0N1y0
# But actually for output layer: each output mult gets input from ALL hidden activations
# So Mul_...y0 (for output y0) gets W_H0N0y0 (from hidden neuron 0) and W_H0N1y0 (from hidden neuron 1)

mult_out = MockNode("Mul_H0N0y0")
w_h0n0_y0 = MockNode("W_H0N0y0")  # Weight from hidden neuron 0 to output 0
w_h0n1_y0 = MockNode("W_H0N1y0")  # Weight from hidden neuron 1 to output 0

# These weights are predecessors of the SAME mult node
mult_out.predecessors = [w_h0n0_y0, w_h0n1_y0]

nodes2 = [mult_out, w_h0n0_y0, w_h0n1_y0]
engine2 = MLPLayoutEngine(nodes2, grid_size=80)
engine2.place_node(mult_out, 10, 0)

print(f"mult at grid: {engine2.get_grid_coords(mult_out)}")
engine2._place_weights_for_mults([mult_out], 10)

print(f"W_H0N0y0 grid: {engine2.get_grid_coords(w_h0n0_y0)}")
print(f"W_H0N1y0 grid: {engine2.get_grid_coords(w_h0n1_y0)}")
print(
    f"Different positions? {engine2.get_grid_coords(w_h0n0_y0) != engine2.get_grid_coords(w_h0n1_y0)}"
)

# Test 3: Check if the issue is with find_nodes_by_pattern for output mults
print("\n" + "=" * 50)
print("TEST 3: Pattern matching for output mult nodes")
print("=" * 50)

import re

test_names = ["Mul_H0N0y0", "Mul_H0N1y0", "Mul_x0H0N0", "Mul_H0N0H1N0"]
pattern = r"^Mul_H\d+N\d+y\d+$"
for name in test_names:
    match = re.match(pattern, name)
    print(f"{name}: matches output pattern? {bool(match)}")
