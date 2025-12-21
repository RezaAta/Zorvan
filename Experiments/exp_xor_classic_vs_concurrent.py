"""
Comparison: Classic MLP vs Concurrent Computational Graph MLP on XOR problem
(This file was moved from `ComputationalGraphs/Tests/MLPTests/test_xor_classic_vs_concurrent.py`)
"""

import random
import time

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score

# Classic MLP import
from ClassicMLP import ClassicMLP
from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor

# Computational Graph imports
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode

print("=" * 80)
print("XOR PROBLEM: CLASSIC MLP vs CONCURRENT COMPUTATIONAL GRAPH (FIXED)")
print("=" * 80)
print("\nConfiguration from TestingOnXOR.py:")
print("  Architecture: 2-2-1 (2 inputs, 2 hidden neurons, 1 output)")
print("  Hidden Activation: Sigmoid")
print("  Output Activation: Linear")
print("  Learning Rate: 0.5")
print("  Training: 2000 epochs x 4 iterations = 8000 total iterations")
print("=" * 80)

# XOR Dataset
# Graph format: row-per-feature
X_graph = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]
y_graph = [[0.0, 1.0, 1.0, 0.0]]

# Classic format: row-per-sample
X_classic = np.array([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])
y_classic = np.array([[0.0], [1.0], [1.0], [0.0]])

ground_truth = np.array([0, 1, 1, 0])

# ============================================================================
# TEST 1: CLASSIC MLP
# ============================================================================
print("\n[1/2] CLASSIC MLP")
print("-" * 80)

# Match graph configuration exactly: 2 inputs, 1 hidden layer with 2 neurons, 1 output
# Set seed for Classic MLP (uses np.random)
np.random.seed(42)
classic_mlp = ClassicMLP(
    input_size=2,
    hidden_layers=[2],  # Match default: [numInputs] = [2]
    output_size=1,
    hidden_activation="sigmoid",
    output_activation="linear",
    learning_rate=0.1,
    use_bias=True,
)

print("\nClassic MLP Initial Weights:")
print("  Hidden layer weights (2x2):")
print(classic_mlp.weights[0])
print("  Output layer weights (2x1):")
print(classic_mlp.weights[1])

# Save initial weights BEFORE training for concurrent graph
classic_initial_hidden = classic_mlp.weights[0].copy()
classic_initial_output = classic_mlp.weights[1].copy()

print("Training Classic MLP...")
start_time = time.time()

# Train with batch_size=1 (SGD) to match the sample-by-sample processing
# Classic MLP with batch_size=4 and lr=0.5 diverges, but SGD works well
mse_history_classic = classic_mlp.train(X_classic, y_classic, epochs=5000, batch_size=1)

classic_time = time.time() - start_time

# Predictions
predictions_classic = classic_mlp.predict(X_classic).flatten()
predictions_binary_classic = (predictions_classic > 0.5).astype(int)

# Metrics
precision_classic = precision_score(
    ground_truth, predictions_binary_classic, zero_division=0
)
recall_classic = recall_score(ground_truth, predictions_binary_classic, zero_division=0)
f1_classic = f1_score(ground_truth, predictions_binary_classic, zero_division=0)
mae_classic = np.mean(np.abs(ground_truth - predictions_classic))
final_mse_classic = mse_history_classic[-1]

print(f"Training Time: {classic_time:.4f}s")
print(f"Final MSE: {final_mse_classic:.6f}")
print(
    f"Metrics - Precision: {precision_classic:.4f}, Recall: {recall_classic:.4f}, F1: {f1_classic:.4f}"
)
print(f"MAE: {mae_classic:.4f}")
print("\nPredictions:")
for i in range(len(X_classic)):
    print(
        f"  [{X_classic[i,0]:.1f}, {X_classic[i,1]:.1f}] -> {predictions_classic[i]:.4f} (Binary: {predictions_binary_classic[i]}) | True: {ground_truth[i]}"
    )

# ============================================================================
# TEST 2: CONCURRENT COMPUTATIONAL GRAPH (WITH FIXED BACKPROP)
# ============================================================================
print("\n[2/2] CONCURRENT COMPUTATIONAL GRAPH (FIXED)")
print("-" * 80)

# Build MLP Graph - exact configuration from TestingOnXOR.py
# Set seed for Concurrent Graph (uses random.uniform)
random.seed(42)
mlpGraph = MLPGraph(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    # hiddenLayerSizes not specified -> defaults to [numInputs] = [2]
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,
)
mlpGraph.BuildMLP()

# Build Backprop Graph with FIXED connections
backprop_graph = BackpropGraph(mlpGraph, learningRate=0.1)
backprop_graph.BuildBackprop()

# Load data
mlpGraph.LoadData(X_graph, y_graph)

# Combine graphs
fullMLPGraph = Graph()
for node in mlpGraph.nodes:
    fullMLPGraph.AddNode(node)
for node in backprop_graph.nodes:
    fullMLPGraph.AddNode(node)
fullMLPGraph.UpdateAdjacencyMatrix()

# Copy INITIAL weights from Classic MLP to Concurrent Graph for identical initialization
print("Copying initial weights from Classic MLP to Concurrent Graph...")
for node in mlpGraph.nodes:
    # Hidden layer weights: W_x{input}H0N{neuron}
    if node.name.startswith("W_x") and "H0N" in node.name:
        input_idx = int(node.name[3])
        neuron_idx = int(node.name.split("H0N")[1])
        node.value = classic_initial_hidden[input_idx, neuron_idx]
    # Output layer weights: W_H0N{hidden}y{output}
    elif node.name.startswith("W_H0N") and "y" in node.name:
        hidden_idx = int(node.name.split("W_H0N")[1].split("y")[0])
        output_idx = int(node.name.split("y")[1])
        node.value = classic_initial_output[hidden_idx, output_idx]

print("\nConcurrent Graph Initial Weights (after copy from Classic):")
# Extract weight matrix format to verify copy - check fullMLPGraph nodes
hidden_weights = np.zeros((2, 2))  # (inputs x hidden)
output_weights = np.zeros((2, 1))  # (hidden x output)

for node in fullMLPGraph.nodes:  # Check fullMLPGraph instead of mlpGraph
    # Hidden layer weights: W_x{input}H0N{neuron}
    if node.name.startswith("W_x") and "H0N" in node.name:
        input_idx = int(node.name[3])
        neuron_idx = int(node.name.split("H0N")[1])
        hidden_weights[input_idx, neuron_idx] = node.value
    # Output layer weights: W_H0N{hidden}y{output}
    elif node.name.startswith("W_H0N") and "y" in node.name:
        hidden_idx = int(node.name.split("W_H0N")[1].split("y")[0])
        output_idx = int(node.name.split("y")[1])
        output_weights[hidden_idx, output_idx] = node.value

print("  Hidden layer weights (2x2):")
print(hidden_weights)
print("  Output layer weights (2x1):")
print(output_weights)

# Initialize processors
mlpProcessor = GraphProcessor(mlpGraph, verbose=False, visual=False)
fullGraphProcessor = GraphProcessor(fullMLPGraph, verbose=False, visual=False)

print(f"Total nodes: {len(fullMLPGraph.nodes)}")
print(f"Auto-selected workers: {fullGraphProcessor.max_workers}")
print(f"Single-thread mode: {fullGraphProcessor.use_single_thread_mode}")

# Network warmup
networkLength = 3 * (len(mlpGraph.hiddenLayers) + 1)
mlpProcessor.ComputeGraph(networkLength)

# Training - exact configuration from TestingOnXOR.py
print("Training Concurrent Graph...")
fakeBatchSize = 1
epochs = 5000
numberOfIterationsInEpochs = 4
totalIterations = epochs * numberOfIterationsInEpochs * fakeBatchSize

mlpGraph.CreateErrorBuffers(totalIterations, mse_buffer_size=numberOfIterationsInEpochs)
errorBuffers = mlpGraph.errorBuffers
for eb in errorBuffers:
    if eb not in fullMLPGraph.nodes:
        fullMLPGraph.AddNode(eb)
if hasattr(mlpGraph, "mseNodes"):
    for mse_node in mlpGraph.mseNodes:
        if mse_node not in fullMLPGraph.nodes:
            fullMLPGraph.AddNode(mse_node)

start_time = time.time()
fullGraphProcessor.ComputeGraph(totalIterations + 1)
graph_time = time.time() - start_time

# Calculate MSE over epochs
MSEOverEpochs = []
for i in range(totalIterations):
    mse = 0
    for errorBuffer in errorBuffers:
        mse += (errorBuffer.buffer[i]) ** 2
    mse = mse / len(errorBuffers)
    MSEOverEpochs.append(mse)

MSEOverEpochs = np.array(MSEOverEpochs)
newMSEOverEpochs = MSEOverEpochs.reshape(-1, numberOfIterationsInEpochs * fakeBatchSize)
mse_history_graph = np.mean(newMSEOverEpochs, axis=1)

# Test predictions
mlpGraph.PrepareForTest(X_graph, y_graph)
predictionBuffers = mlpGraph.predictionBuffers
testingEpochs = len(X_graph[0]) + networkLength
mlpProcessor.ComputeGraph(testingEpochs)

predictions_graph = np.array(predictionBuffers[0].buffer)
predictions_binary_graph = (predictions_graph > 0.5).astype(int)

# Metrics
precision_graph = precision_score(
    ground_truth, predictions_binary_graph, zero_division=0
)
recall_graph = recall_score(ground_truth, predictions_binary_graph, zero_division=0)
f1_graph = f1_score(ground_truth, predictions_binary_graph, zero_division=0)
mae_graph = np.mean(np.abs(ground_truth - predictions_graph))
final_mse_graph = mse_history_graph[-1]

print(f"Training Time: {graph_time:.4f}s")
print(f"Final MSE: {final_mse_graph:.6f}")
print(
    f"Metrics - Precision: {precision_graph:.4f}, Recall: {recall_graph:.4f}, F1: {f1_graph:.4f}"
)
print(f"MAE: {mae_graph:.4f}")
print("\nPredictions:")
for i in range(len(X_graph[0])):
    print(
        f"  [{X_graph[0][i]:.1f}, {X_graph[1][i]:.1f}] -> {predictions_graph[i]:.4f} (Binary: {predictions_binary_graph[i]}) | True: {ground_truth[i]}"
    )

# ============================================================================
# COMPARISON SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)
print(f"{'Metric':<30} {'Classic MLP':<20} {'Concurrent Graph':<20} {'Difference'}")
print("-" * 80)
print(
    f"{'Training Time (s)':<30} {classic_time:<20.4f} {graph_time:<20.4f} {abs(classic_time - graph_time):.4f}"
)
print(
    f"{'Final MSE':<30} {final_mse_classic:<20.6f} {final_mse_graph:<20.6f} {abs(final_mse_classic - final_mse_graph):.6f}"
)
print(
    f"{'Precision':<30} {precision_classic:<20.4f} {precision_graph:<20.4f} {abs(precision_classic - precision_graph):.4f}"
)
print(
    f"{'Recall':<30} {recall_classic:<20.4f} {recall_graph:<20.4f} {abs(recall_classic - recall_graph):.4f}"
)
print(
    f"{'F1 Score':<30} {f1_classic:<20.4f} {f1_graph:<20.4f} {abs(f1_classic - f1_graph):.4f}"
)
print(
    f"{'MAE':<30} {mae_classic:<20.4f} {mae_graph:<20.4f} {abs(mae_classic - mae_graph):.4f}"
)

# Analyze convergence
if final_mse_classic < 0.3 and final_mse_graph < 0.3:
    print("\nResult: Both implementations converged successfully!")
elif final_mse_classic < 0.3:
    print(
        "\nResult: Classic MLP converged, but Concurrent Graph did not (likely gradient delay)"
    )
elif final_mse_graph < 0.3:
    print("\nResult: Concurrent Graph converged, but Classic MLP did not")
else:
    print("\nResult: Neither implementation converged - both stuck at high MSE")
    print(
        "Note: Linear output activation cannot solve XOR (needs sigmoid for binary classification)"
    )

print("=" * 80)

# ============================================================================
# PLOT LEARNING CURVES
# ============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Linear scale
axes[0].plot(
    mse_history_classic, label="Classic MLP", linewidth=2, alpha=0.8, color="blue"
)
axes[0].plot(
    mse_history_graph,
    label="Concurrent Graph (FIXED)",
    linewidth=2,
    alpha=0.8,
    color="orange",
)
axes[0].set_xlabel("Epoch", fontsize=12)
axes[0].set_ylabel("Mean Squared Error", fontsize=12)
axes[0].set_title(
    "Learning Curves Comparison (Linear Scale)", fontsize=14, fontweight="bold"
)
axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)

# Log scale
axes[1].plot(
    mse_history_classic, label="Classic MLP", linewidth=2, alpha=0.8, color="blue"
)
axes[1].plot(
    mse_history_graph,
    label="Concurrent Graph (FIXED)",
    linewidth=2,
    alpha=0.8,
    color="orange",
)
axes[1].set_xlabel("Epoch", fontsize=12)
axes[1].set_ylabel("Mean Squared Error", fontsize=12)
axes[1].set_title(
    "Learning Curves Comparison (Log Scale)", fontsize=14, fontweight="bold"
)
axes[1].set_yscale("log")
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("xor_classic_vs_concurrent_comparison.png", dpi=150, bbox_inches="tight")
print("\nLearning curves saved to: xor_classic_vs_concurrent_comparison.png")
plt.show()

print("\nTEST COMPLETE")
