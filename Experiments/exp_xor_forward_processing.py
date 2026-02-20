# Moved from zorvan/Tests/MLPTests/TestingForwardProcessingOnXOR.py
# Renamed to Experiments/exp_xor_forward_processing.py

"""
Test MLPGraphForwardProcessing on XOR Problem
Benchmark test matching the structure of existing XOR tests for comparison.
"""

import time

import matplotlib.pyplot as plt
import numpy as np

from zorvan.Core.BackpropGraphForwardProcessing import BackpropGraphForwardProcessing
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.SigmoidNode import SigmoidNode

print("=" * 70)
print("Testing MLPGraphForwardProcessing on XOR Problem")
print("=" * 70)

# XOR dataset
X_train = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
y_train = [[0.0], [1.0], [1.0], [0.0]]

# Hyperparameters (matching Examples/exp_xor_classic_mlp.py)
hidden_layers = [2, 2, 2]
learning_rate = 0.5
epochs = 2000

print(f"\nHyperparameters:")
print(f"  Hidden layers: {hidden_layers}")
print(f"  Learning rate: {learning_rate}")
print(f"  Epochs: {epochs}")
print(f"  Activation: Sigmoid")

# Create MLP without buffers
print("\nBuilding MLP (no buffers, forward processing)...")
mlp = MLPGraphForwardProcessing(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    # hiddenLayerSizes=hidden_layers,
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,  # Linear output for regression
)
mlp.BuildMLP()

print(f"MLP built: {len(mlp.nodes)} nodes")

# Create backprop graph
print("Building Backprop graph (no buffers)...")
backprop = BackpropGraphForwardProcessing(mlp, learningRate=learning_rate)
backprop.BuildBackprop()

print(f"Backprop built: {len(backprop.nodes)} nodes")

# Combine graphs
fullGraph = Graph()
for node in mlp.nodes:
    fullGraph.AddNode(node)
for node in backprop.nodes:
    fullGraph.AddNode(node)

# IMPORTANT: For TRAINING, starting nodes are first-layer multiplications + labels + LR
# First-layer multiplication nodes are the FIRST COMPUTATION (inputs * weights)
# Labels needed for error calculation, LR needed for gradient scaling
fullGraph.starting_nodes = mlp.starting_nodes + [backprop.lrNode]

print(f"Full graph: {len(fullGraph.nodes)} nodes")

# Create processor
processor = GraphProcessor(fullGraph, verbose=False)

# Show iteration calculation
print("\n" + "=" * 70)
print("Iteration Calculation")
print("=" * 70)
required_forward = mlp.GetRequiredIterations()
required_full = mlp.GetRequiredIterationsWithBackprop()
print(f"Required iterations (forward pass only): {required_forward}")
print(f"Required iterations (with backprop): {required_full}")

# Training with manual sample loading
print("\n" + "=" * 70)
print("Training (Manual Sample Loop)")
print("=" * 70)

# Load ALL data once - DataStreamNodes will cycle through it automatically
print("Loading all training data into DataStreamNodes...")
mlp.LoadData(X_train, y_train)

# Prepare forward-processing graph so starting nodes can read source/container values
# This marks DataStream source nodes and Container weight nodes as 'processed'
# so the first computation nodes (multiplications) can execute immediately.
prep_counts = mlp.PrepareForForwardProcessing(processor)
print(
    f"PrepareForForwardProcessing marked: sources={prep_counts[0]}, containers={prep_counts[1]}"
)

# Calculate iterations needed
iterations_per_sample = mlp.GetPassLength()
num_samples = len(X_train)
iterations_per_epoch = iterations_per_sample * num_samples
total_iterations = iterations_per_epoch * epochs

print(f"Iterations per sample: {iterations_per_sample}")
print(f"Samples per epoch: {num_samples}")
print(f"Iterations per epoch: {iterations_per_epoch}")
print(f"Total iterations: {total_iterations}")

# We'll attach error buffers to the error layer and run the entire training
# inside the graph as a single continuous ForwardProcessing call (no epoch loop).

# Create error buffers that store per-iteration error values
error_buffers = mlp.CreateErrorBuffers(
    total_iterations, allowNone=True, mse_buffer_size=len(X_train)
)
for eb in error_buffers:
    if eb not in fullGraph.nodes:
        fullGraph.AddNode(eb)
if hasattr(mlp, "mseNodes"):
    for m in mlp.mseNodes:
        if m not in fullGraph.nodes:
            fullGraph.AddNode(m)

# Rebuild adjacency maps to include new buffers
fullGraph.UpdateAdjacencyMatrix()

print("\nRunning continuous training inside the graph (single call)...")
start_time = time.time()

# Run entire training as one continuous run
processor.ForwardProcessing(iterations=total_iterations)

training_time = time.time() - start_time
print(f"\nTraining completed in {training_time:.2f} seconds")
if training_time > 0:
    print(f"Iterations per second: {int(total_iterations / training_time)}")

# Build epoch-wise MSE history from error buffer(s)
mse_history = []
if error_buffers:
    # Assume single output (XOR) -> single error buffer
    buf = error_buffers[0]
    # buf.buffer contains the oldest-first elements; ensure length
    errors = [v for v in buf.buffer if v is not None]
    # If recorded errors are less than expected, pad with Nones
    if len(errors) < total_iterations:
        # try to use raw buffer (may contain None if bufferSize larger than appended)
        errors = list(buf.buffer)

    # Compute per-epoch MSE by windowing
    for e in range(epochs):
        start = e * iterations_per_epoch
        end = start + iterations_per_epoch
        window = errors[start:end]
        # filter out None values
        window_vals = [x for x in window if x is not None]
        if window_vals:
            mse_history.append(float(np.mean([x**2 for x in window_vals])))
        else:
            mse_history.append(0.0)
else:
    mse_history = [0.0] * epochs

# Debug: print error buffer contents summary
print("\nError buffer summary:")
for i, buf in enumerate(error_buffers):
    total = len(buf.buffer)
    non_none = len([v for v in buf.buffer if v is not None])
    sample_vals = buf.buffer[: min(40, total)]
    print(f"  Buffer {i}: size={total}, non-None={non_none}")
    print(f"    first {min(10,total)} values: {sample_vals[:10]}")

# Testing - run inference on each sample
print("\n" + "=" * 70)
print("Testing")
print("=" * 70)

predictions = []
ground_truth = []
test_mae = 0.0

# Testing - DataStreamNodes already have the data loaded, just need to reset and run
print(f"Running inference for {len(X_train)} samples...")

# Reset DataStreamNodes to start from beginning
mlp.LoadData(X_train, y_train)  # Reload to reset stream indices

# Reset processor
processor.reset_forward_state()

# Run inference for all samples
forward_only = mlp.GetRequiredIterations()

# Rest of file continues...
