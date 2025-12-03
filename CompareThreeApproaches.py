"""
3-Way Performance Comparison on XOR Dataset:
1. Classic (Pure NumPy - NO computational graphs)
2. Default Computational Graph (BufferNodes + temporal delays)
3. Forward Processing (New computational graph - NO buffers, NO delays)
"""

import time

import matplotlib.pyplot as plt
import numpy as np

from ClassicMLP import ClassicMLP
from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.BackpropGraphForwardProcessing import (
    BackpropGraphForwardProcessing,
)
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode

print("=" * 80)
print("3-WAY PERFORMANCE COMPARISON")
print("=" * 80)

# XOR dataset
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([[0], [1], [1], [0]])

# Configuration
hidden_layers = [4]
learning_rate = 0.5
epochs = 100  # Reduced for faster comparison

# ============================================================================
# 1. CLASSIC MLP (Pure NumPy - NO computational graphs)
# ============================================================================
print("\n1. CLASSIC (Pure NumPy - NO computational graphs)")
print("-" * 80)

mlp_classic = ClassicMLP(
    input_size=2,
    output_size=1,
    hidden_layers=hidden_layers,
    hidden_activation="sigmoid",
    output_activation="linear",
    learning_rate=learning_rate,
    use_bias=False,
)

# Track MSE over epochs
classic_mse_history = []

start = time.perf_counter()
for epoch in range(epochs):
    epoch_mse = 0
    for i in range(len(X)):
        x_sample = X[i : i + 1]
        y_sample = y[i : i + 1]
        # Use forward_pass and backward_pass directly to avoid verbose output
        activations = mlp_classic.forward_pass(x_sample)
        mlp_classic.backward_pass(x_sample, y_sample, activations)
        # Calculate MSE for this sample
        epoch_mse += np.mean((activations[-1] - y_sample) ** 2)
    # Average MSE for the epoch
    classic_mse_history.append(epoch_mse / len(X))
classic_time = time.perf_counter() - start

total_iterations = epochs * len(X)
classic_per_iter = classic_time / total_iterations * 1000

print(f"Time: {classic_time:.4f}s")
print(f"Iterations/sec: {total_iterations/classic_time:.2f}")
print(f"Time per iteration: {classic_per_iter:.4f}ms")

# Test predictions
predictions_classic = mlp_classic.predict(X)
mae_classic = np.mean(np.abs(predictions_classic - y))
print(f"Final MSE: {classic_mse_history[-1]:.6f}")
print(f"Test MAE: {mae_classic:.6f}")

# ============================================================================
# 2. DEFAULT COMPUTATIONAL GRAPH (BufferNodes + temporal delays)
# ============================================================================
print("\n2. DEFAULT COMPUTATIONAL GRAPH (BufferNodes + temporal delays)")
print("-" * 80)

mlp_default = MLPGraph(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    hiddenLayerSizes=[4],
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,
)
mlp_default.BuildMLP()  # Build the MLP graph structure

backprop_default = BackpropGraph(mlpGraph=mlp_default, learningRate=learning_rate)
backprop_default.BuildBackprop()  # Build the backprop graph structure

# Combine graphs
graph_default = Graph()
for node in mlp_default.nodes:
    graph_default.AddNode(node)
for node in backprop_default.nodes:
    graph_default.AddNode(node)

processor_default = GraphProcessor(graph_default, verbose=False)

print(f"Total nodes: {len(graph_default.nodes)}")
print(f"Uses BufferNodes: Yes")
print(f"Temporal delay: 3*(layers+1) = {3*(1+2)} timesteps")

# Load all data at once (transposed format: rows=features, cols=samples)
X_transposed = (
    X.T.tolist()
)  # [[x1_sample1, x1_sample2, ...], [x2_sample1, x2_sample2, ...]]
y_transposed = y.T.tolist()  # [[y_sample1, y_sample2, ...]]
mlp_default.LoadData(X_transposed, y_transposed)

# Create error buffers for tracking. We want MSE node buffer size = dataset size
mlp_default.CreateErrorBuffers(total_iterations, mse_buffer_size=len(X_transposed[0]))
errorBuffers = mlp_default.errorBuffers
for errorBuffer in errorBuffers:
    graph_default.AddNode(errorBuffer)
if hasattr(mlp_default, "mseNodes"):
    for mse_node in mlp_default.mseNodes:
        graph_default.AddNode(mse_node)

# Network warmup - fill buffers with initial values
networkLength = 3 * (mlp_default.numHiddenLayers + 1)
processor_default.ComputeGraph(networkLength)

# Training - Default graph processes ALL iterations in one call
# This is how it's designed: it streams through data using BufferNodes
start = time.perf_counter()
processor_default.ComputeGraph(total_iterations)
default_time = time.perf_counter() - start

default_per_iter = default_time / total_iterations * 1000

print(f"Time: {default_time:.4f}s")
print(f"Iterations/sec: {total_iterations/default_time:.2f}")
print(f"Time per iteration: {default_per_iter:.4f}ms")

# Extract MSE over epochs from error buffers
default_mse_history = []
for i in range(total_iterations):
    mse = 0
    for errorBuffer in errorBuffers:
        mse += (errorBuffer.buffer[i]) ** 2
    mse = mse / len(errorBuffers)
    default_mse_history.append(mse)

# Average MSE per epoch
default_mse_per_epoch = (
    np.array(default_mse_history).reshape(epochs, len(X)).mean(axis=1)
)

# Test predictions - compute from last hidden layer through output weights
# The buffers contain: warmup values + all training iterations
# We want the last 4 samples (one epoch) from the training
predictions_default = []
last_hidden_layer = mlp_default.hiddenLayers[-1]

# Check buffer size
sample_buffer = last_hidden_layer[0][2].buffer
print(
    f"Buffer size: {len(sample_buffer)}, Expected: {networkLength + total_iterations}"
)

# Get predictions from the END of the buffer (last epoch)
for sample_idx in range(len(X)):
    # Index from the end: last epoch's samples are at the very end
    buffer_idx = len(sample_buffer) - len(X) + sample_idx

    # Sum up weighted inputs to output (same as what AdditionNode does)
    output_sum = 0
    for neuron_idx, (addNode, actNode, bufNode) in enumerate(last_hidden_layer):
        # Get activation value from buffer at the specific iteration
        activation = bufNode.buffer[buffer_idx]
        # Get corresponding weight
        weight = mlp_default.weightLayers[-1][neuron_idx][0].value
        output_sum += activation * weight

    # Apply output activation (Linear just returns the value)
    predictions_default.append(output_sum)

predictions_default = np.array(predictions_default)
mae_default = np.mean(np.abs(predictions_default.flatten() - y.flatten()))
print(f"Final MSE: {default_mse_per_epoch[-1]:.6f}")
print(f"Test MAE: {mae_default:.6f}")

# ============================================================================
# 3. FORWARD PROCESSING (New approach - NO buffers, NO delays)
# ============================================================================
print("\n3. FORWARD PROCESSING (New computational graph - NO buffers, NO delays)")
print("-" * 80)

mlp_forward = MLPGraphForwardProcessing(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    hiddenLayerSizes=hidden_layers,
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,
)
mlp_forward.BuildMLP()

backprop_forward = BackpropGraphForwardProcessing(
    mlpGraph=mlp_forward, learningRate=learning_rate
)
backprop_forward.BuildBackprop()

# Combine graphs
graph_forward = Graph()
for node in mlp_forward.nodes:
    graph_forward.AddNode(node)
for node in backprop_forward.nodes:
    graph_forward.AddNode(node)
# Create MSE nodes for forward graph (use dataset size = len(X))
try:
    mlp_forward.CreateErrorBuffers(total_iterations, allowNone=True, mse_buffer_size=len(X))
    for m in mlp_forward.mseNodes:
        graph_forward.AddNode(m)
except Exception:
    pass

processor_forward = GraphProcessor(graph_forward, verbose=False)

print(f"Total nodes: {len(graph_forward.nodes)}")
print(f"Uses BufferNodes: No")
print(f"Temporal delay: 0 timesteps (immediate)")

# Calculate network depth: need enough timesteps for signal to propagate through
# For MLP: input -> hidden layers -> output -> error -> backprop through layers
# Approximate depth = 2 * (num_hidden_layers + 1) for forward + backward pass
network_depth_forward = 2 * (
    mlp_forward.numHiddenLayers + 2
)  # +2 for input and output layers
print(f"Network depth (timesteps per sample): {network_depth_forward}")

# Calculate actual total iterations needed
total_timesteps_forward = total_iterations * network_depth_forward
print(f"Total timesteps needed: {total_timesteps_forward}")

start = time.perf_counter()
for epoch in range(epochs):
    for i in range(len(X)):
        mlp_forward.LoadData(X[i], y[i])
        processor_forward.ForwardProcessing(iterations=network_depth_forward)
forward_time = time.perf_counter() - start

# Adjust metrics to show per training sample (not per timestep)
forward_per_sample = forward_time / total_iterations * 1000
forward_per_timestep = forward_time / total_timesteps_forward * 1000

print(f"Time: {forward_time:.4f}s")
print(f"Training samples/sec: {total_iterations/forward_time:.2f}")
print(f"Time per training sample: {forward_per_sample:.4f}ms")
print(f"Time per timestep: {forward_per_timestep:.4f}ms")

# For comparison purposes, use time per training sample
forward_per_iter = forward_per_sample

# Calculate MSE from error nodes (need to track during training)
# For now, compute final predictions and MSE
forward_mse_history = []
for epoch in range(epochs):
    epoch_mse = 0
    for i in range(len(X)):
        mlp_forward.LoadData(X[i], y[i])
        processor_forward.ForwardProcessing(iterations=network_depth_forward)
        # Get prediction
        output_node = (
            mlp_forward.outputLayer[0][0]
            if isinstance(mlp_forward.outputLayer[0], tuple)
            else mlp_forward.outputLayer[0]
        )
        prediction = output_node.value
        epoch_mse += (prediction - y[i][0]) ** 2
    forward_mse_history.append(epoch_mse / len(X))

# Test predictions
predictions_forward = []
for i in range(len(X)):
    mlp_forward.LoadData(X[i], y[i])
    processor_forward.ForwardProcessing(iterations=network_depth_forward)
    output_node = (
        mlp_forward.outputLayer[0][0]
        if isinstance(mlp_forward.outputLayer[0], tuple)
        else mlp_forward.outputLayer[0]
    )
    predictions_forward.append(output_node.value)

predictions_forward = np.array(predictions_forward)
mae_forward = np.mean(np.abs(predictions_forward.flatten() - y.flatten()))
print(f"Final MSE: {forward_mse_history[-1]:.6f}")
print(f"Test MAE: {mae_forward:.6f}")

# ============================================================================
# COMPARISON
# ============================================================================
print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

print(f"\n{'Method':<40} {'Time/iter':<15} {'Relative':<15}")
print("-" * 80)
print(f"{'Classic (Pure NumPy)':<40} {classic_per_iter:>10.4f} ms  {1.0:>10.2f}x")
print(
    f"{'Default Graph (BufferNodes)':<40} {default_per_iter:>10.4f} ms  {default_per_iter/classic_per_iter:>10.2f}x"
)
print(
    f"{'Forward Processing (No Buffers)':<40} {forward_per_iter:>10.4f} ms  {forward_per_iter/classic_per_iter:>10.2f}x"
)

print("\n" + "-" * 80)
print("Key Comparisons:")
print("-" * 80)

# Compare computational graph approaches
if forward_per_iter < default_per_iter:
    speedup = default_per_iter / forward_per_iter
    print(f"Forward Processing is {speedup:.2f}x FASTER than Default Graph")
    print(
        f"   Overhead eliminated: {default_per_iter - forward_per_iter:.4f}ms per iteration"
    )
else:
    slowdown = forward_per_iter / default_per_iter
    print(f"Forward Processing is {slowdown:.2f}x SLOWER than Default Graph")
    print(
        f"   Additional overhead: {forward_per_iter - default_per_iter:.4f}ms per iteration"
    )

print()

# Compare to classic baseline
if forward_per_iter < classic_per_iter:
    speedup = classic_per_iter / forward_per_iter
    print(f"Forward Processing is {speedup:.2f}x FASTER than Classic NumPy")
elif forward_per_iter > classic_per_iter:
    slowdown = forward_per_iter / classic_per_iter
    print(f"Forward Processing is {slowdown:.2f}x SLOWER than Classic NumPy")
    print(
        f"   Graph overhead: {forward_per_iter - classic_per_iter:.4f}ms per iteration"
    )
else:
    print("Forward Processing matches Classic NumPy performance")

print()

if default_per_iter > forward_per_iter:
    overhead = default_per_iter - forward_per_iter
    print(f"BufferNode overhead: {overhead:.4f}ms per iteration")
    print(f"   This is the cost of temporal delay functionality")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

# ============================================================================
# LEARNING CURVES VISUALIZATION
# ============================================================================
print("\nGenerating learning curves...")

plt.figure(figsize=(12, 5))

# Plot 1: MSE over epochs
plt.subplot(1, 2, 1)
plt.plot(
    range(1, epochs + 1),
    classic_mse_history,
    "b-",
    label="Classic (NumPy)",
    linewidth=2,
)
plt.plot(
    range(1, epochs + 1),
    default_mse_per_epoch,
    "r-",
    label="Default Graph (BufferNodes)",
    linewidth=2,
)
plt.plot(
    range(1, epochs + 1),
    forward_mse_history,
    "g-",
    label="Forward Processing",
    linewidth=2,
)
plt.xlabel("Epoch")
plt.ylabel("MSE")
plt.title("Learning Curves - MSE over Epochs")
plt.legend()
plt.grid(True, alpha=0.3)
plt.yscale("log")  # Log scale to better see convergence

# Plot 2: Final comparison
plt.subplot(1, 2, 2)
models = ["Classic\n(NumPy)", "Default Graph\n(BufferNodes)", "Forward\nProcessing"]
times = [classic_per_iter, default_per_iter, forward_per_iter]
maes = [mae_classic, mae_default, mae_forward]

x_pos = np.arange(len(models))
fig, ax1 = plt.subplots()

color = "tab:blue"
ax1.set_xlabel("Model")
ax1.set_ylabel("Time per iteration (ms)", color=color)
ax1.bar(x_pos, times, alpha=0.6, color=color)
ax1.tick_params(axis="y", labelcolor=color)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(models)

ax2 = ax1.twinx()
color = "tab:red"
ax2.set_ylabel("MAE", color=color)
ax2.plot(x_pos, maes, "ro-", linewidth=2, markersize=8)
ax2.tick_params(axis="y", labelcolor=color)

plt.title("Performance & Accuracy Comparison")
plt.tight_layout()

plt.show()

print("\nFinal Metrics Summary:")
print("=" * 80)
print(f"{'Model':<30} {'Final MSE':<15} {'MAE':<15} {'Time/iter (ms)':<15}")
print("=" * 80)
print(
    f"{'Classic (NumPy)':<30} {classic_mse_history[-1]:<15.6f} {mae_classic:<15.6f} {classic_per_iter:<15.4f}"
)
print(
    f"{'Default Graph (BufferNodes)':<30} {default_mse_per_epoch[-1]:<15.6f} {mae_default:<15.6f} {default_per_iter:<15.4f}"
)
print(
    f"{'Forward Processing':<30} {forward_mse_history[-1]:<15.6f} {mae_forward:<15.6f} {forward_per_iter:<15.4f}"
)
print("=" * 80)
