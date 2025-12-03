"""
3-Way Performance Comparison on Diabetes Dataset:
1. Classic (Pure NumPy - NO computational graphs)
2. Default Computational Graph (BufferNodes + temporal delays)
3. Forward Processing (New computational graph - NO buffers, NO delays)
"""

import time

import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ClassicMLP import ClassicMLP
from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.BackpropGraphForwardProcessing import (
    BackpropGraphForwardProcessing,
)
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode

print("=" * 80)
print("DIABETES DATASET - PERFORMANCE COMPARISON")
print("=" * 80)

# Load and preprocess Diabetes Dataset
data = load_diabetes()
X = data.data
y = data.target.reshape(-1, 1)

# Detect and remove outliers using IQR
q1 = np.percentile(y, 25, axis=0)
q3 = np.percentile(y, 75, axis=0)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

non_outlier_mask = (y >= lower_bound) & (y <= upper_bound)
X = X[non_outlier_mask.flatten()]
y = y[non_outlier_mask.flatten()]

# Split and scale
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
scaler_X = StandardScaler()
X_train = scaler_X.fit_transform(X_train)
X_test = scaler_X.transform(X_test)

print(f"\nDataset Info:")
print(f"  Training samples: {len(X_train)}")
print(f"  Test samples: {len(X_test)}")
print(f"  Features: {X_train.shape[1]}")

# Configuration
hidden_layers = [8, 4, 2]
learning_rate = 0.00001
epochs = 100  # Reduced for faster comparison
batch_size = 1

total_iterations = epochs * len(X_train) * batch_size

# ============================================================================
# 1. CLASSIC MLP (Pure NumPy - NO computational graphs)
# ============================================================================
print("\n1. CLASSIC (Pure NumPy - NO computational graphs)")
print("-" * 80)

mlp_classic = ClassicMLP(
    input_size=X_train.shape[1],
    output_size=1,
    hidden_layers=hidden_layers,
    hidden_activation="sigmoid",
    output_activation="linear",
    learning_rate=learning_rate,
    use_bias=False,
)

start = time.perf_counter()
for epoch in range(epochs):
    for i in range(len(X_train)):
        x_sample = X_train[i : i + 1]
        y_sample = y_train[i : i + 1]
        # Use forward_pass and backward_pass directly to avoid verbose output
        activations = mlp_classic.forward_pass(x_sample)
        mlp_classic.backward_pass(x_sample, y_sample, activations)
classic_time = time.perf_counter() - start

classic_per_iter = classic_time / total_iterations * 1000

print(f"Time: {classic_time:.4f}s")
print(f"Iterations/sec: {total_iterations/classic_time:.2f}")
print(f"Time per iteration: {classic_per_iter:.4f}ms")

# Test accuracy
predictions_classic = mlp_classic.predict(X_test)
mae_classic = np.mean(np.abs(predictions_classic - y_test))
print(f"Test MAE: {mae_classic:.4f}")

# ============================================================================
# 2. DEFAULT COMPUTATIONAL GRAPH (BufferNodes + temporal delays)
# ============================================================================
print("\n2. DEFAULT COMPUTATIONAL GRAPH (BufferNodes + temporal delays)")
print("-" * 80)

# Prepare data in transposed format
X_train_transposed = X_train.T.tolist()
y_train_transposed = y_train.T.tolist()

mlp_default = MLPGraph(
    numInputs=X_train.shape[1],
    numOutputs=1,
    numHiddenLayers=len(hidden_layers),
    hiddenLayerSizes=hidden_layers,
    activationFunction=SigmoidNode,
    outputLayerType=SigmoidNode,  # Using Sigmoid for output like the original
)
mlp_default.BuildMLP()

backprop_default = BackpropGraph(mlpGraph=mlp_default, learningRate=learning_rate)
backprop_default.BuildBackprop()

# Combine graphs
graph_default = Graph()
for node in mlp_default.nodes:
    graph_default.AddNode(node)
for node in backprop_default.nodes:
    graph_default.AddNode(node)

processor_default = GraphProcessor(graph_default, verbose=False)

print(f"Total nodes: {len(graph_default.nodes)}")
print(f"Uses BufferNodes: Yes")
print(f"Temporal delay: 3*(layers+1) = {3*(len(hidden_layers)+1)} timesteps")

# Load data
mlp_default.LoadData(X_train_transposed, y_train_transposed)

# Create error buffers (mse buffer size = dataset size = number of training samples)
mlp_default.CreateErrorBuffers(total_iterations, mse_buffer_size=len(X_train))
errorBuffers = mlp_default.errorBuffers
for errorBuffer in errorBuffers:
    graph_default.AddNode(errorBuffer)
if hasattr(mlp_default, "mseNodes"):
    for mse_node in mlp_default.mseNodes:
        graph_default.AddNode(mse_node)

# Network warmup
networkLength = 3 * (mlp_default.numHiddenLayers + 1)
print(f"Warming up network ({networkLength} iterations)...")
processor_default.ComputeGraph(networkLength)

# Training
print(f"Training ({total_iterations} iterations)...")
start = time.perf_counter()
processor_default.ComputeGraph(total_iterations)
default_time = time.perf_counter() - start

default_per_iter = default_time / total_iterations * 1000

print(f"Time: {default_time:.4f}s")
print(f"Iterations/sec: {total_iterations/default_time:.2f}")
print(f"Time per iteration: {default_per_iter:.4f}ms")

# Test accuracy
X_test_transposed = X_test.T.tolist()
y_test_transposed = y_test.T.tolist()
mlp_default.PrepareForTest(X_test_transposed, y_test_transposed)
predictionBuffers = mlp_default.predictionBuffers

testingEpochs = len(X_test) + networkLength
processor_default.ComputeGraph(testingEpochs)

predictions_default = []
for predictionBuffer in predictionBuffers:
    # Filter out None values from the buffer
    valid_predictions = [p for p in predictionBuffer.buffer if p is not None]
    predictions_default.extend(valid_predictions)
predictions_default = np.array(predictions_default)

# Only calculate MAE if we have valid predictions
if len(predictions_default) >= len(X_test):
    predictions_default = predictions_default[: len(X_test)]  # Trim to test set size
    mae_default = np.mean(np.abs(predictions_default.flatten() - y_test.flatten()))
    print(f"Test MAE: {mae_default:.4f}")
else:
    mae_default = float("nan")
    print(
        f"Test MAE: N/A (insufficient predictions: {len(predictions_default)}/{len(X_test)})"
    )

# ============================================================================
# 3. FORWARD PROCESSING (New approach - NO buffers, NO delays)
# ============================================================================
print("\n3. FORWARD PROCESSING (New computational graph - NO buffers, NO delays)")
print("-" * 80)

mlp_forward = MLPGraphForwardProcessing(
    numInputs=X_train.shape[1],
    numOutputs=1,
    numHiddenLayers=len(hidden_layers),
    hiddenLayerSizes=hidden_layers,
    activationFunction=SigmoidNode,
    outputLayerType=SigmoidNode,
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

processor_forward = GraphProcessor(graph_forward, verbose=False)

print(f"Total nodes: {len(graph_forward.nodes)}")
print("Uses BufferNodes: No")
print("Temporal delay: 0 timesteps (immediate)")

# Calculate network depth: need enough timesteps for signal to propagate through
# For MLP: input -> hidden layers -> output -> error -> backprop through layers
network_depth_forward = 2 * (
    mlp_forward.numHiddenLayers + 2
)  # +2 for input and output layers
print(f"Network depth (timesteps per sample): {network_depth_forward}")

# Calculate actual total timesteps needed
total_timesteps_forward = total_iterations * network_depth_forward
print(f"Total timesteps needed: {total_timesteps_forward}")
print(f"Training ({total_iterations} samples, {total_timesteps_forward} timesteps)...")

start = time.perf_counter()
for epoch in range(epochs):
    for i in range(len(X_train)):
        mlp_forward.LoadData(X_train[i], y_train[i])
        processor_forward.ForwardProcessing(iterations=network_depth_forward)
forward_time = time.perf_counter() - start

forward_per_sample = forward_time / total_iterations * 1000
forward_per_timestep = forward_time / total_timesteps_forward * 1000

print(f"Time: {forward_time:.4f}s")
print(f"Training samples/sec: {total_iterations/forward_time:.2f}")
print(f"Time per training sample: {forward_per_sample:.4f}ms")
print(f"Time per timestep: {forward_per_timestep:.4f}ms")

# For comparison purposes, use time per training sample
forward_per_iter = forward_per_sample

# Test accuracy
predictions_forward = []
for i in range(len(X_test)):
    mlp_forward.LoadData(X_test[i], y_test[i])
    processor_forward.ForwardProcessing(iterations=network_depth_forward)
    # outputLayer is a list of tuples (node, container), get the node
    output_node = (
        mlp_forward.outputLayer[0][0]
        if isinstance(mlp_forward.outputLayer[0], tuple)
        else mlp_forward.outputLayer[0]
    )
    predictions_forward.append(output_node.value)

predictions_forward = np.array(predictions_forward)
mae_forward = np.mean(np.abs(predictions_forward.flatten() - y_test.flatten()))
print(f"Test MAE: {mae_forward:.4f}")

# ============================================================================
# COMPARISON
# ============================================================================
print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

print(f"\nMethod                                   Time/iter       Relative      MAE")
print("-" * 80)
print(
    f"Classic (Pure NumPy)                     {classic_per_iter:8.4f} ms        1.00x     {mae_classic:.4f}"
)
print(
    f"Default Graph (BufferNodes)              {default_per_iter:8.4f} ms       {default_per_iter/classic_per_iter:5.2f}x     {mae_default:.4f}"
)
print(
    f"Forward Processing (No Buffers)          {forward_per_iter:8.4f} ms       {forward_per_iter/classic_per_iter:5.2f}x     {mae_forward:.4f}"
)

print("\n" + "-" * 80)
print("Key Comparisons:")
print("-" * 80)

# Compare graph approaches to Classic
default_slowdown = default_per_iter / classic_per_iter
forward_slowdown = forward_per_iter / classic_per_iter
print(f"Default Graph is {default_slowdown:.2f}x SLOWER than Classic")
print(f"   Graph overhead: {default_per_iter - classic_per_iter:.4f}ms per iteration")
print(f"Forward Processing is {forward_slowdown:.2f}x SLOWER than Classic")
print(f"   Graph overhead: {forward_per_iter - classic_per_iter:.4f}ms per iteration")

print()
# Compare Forward Processing to Default Graph
if forward_per_iter > default_per_iter:
    slowdown = forward_per_iter / default_per_iter
    overhead = forward_per_iter - default_per_iter
    print(f"Forward Processing is {slowdown:.2f}x SLOWER than Default Graph")
    print(f"   Additional overhead: {overhead:.4f}ms per iteration")
else:
    speedup = default_per_iter / forward_per_iter
    savings = default_per_iter - forward_per_iter
    print(f"Forward Processing is {speedup:.2f}x FASTER than Default Graph")
    print(f"   Time saved: {savings:.4f}ms per iteration")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
