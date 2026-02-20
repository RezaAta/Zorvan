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
from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor

# Computational Graph imports
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.SigmoidNode import SigmoidNode

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

# Build a small MLPGraph early so we can set the Classic training delay to match the
# graph's input buffer size. We'll reuse this `mlpGraph` for the concurrent test later.
random.seed(42)
mlpGraph = MLPGraph(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,
)
mlpGraph.BuildMLP()
# Legacy delay synchronization removed: ClassicMLP now updates weights/biases immediately (no delay API).

import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--trace",
    action="store_true",
    help="Enable per-epoch tracing and save traces to artifacts/xor_traces/",
)
args = parser.parse_args()
TRACE = args.trace

print("Training Classic MLP...")
start_time = time.time()

epochs = 5000
batch_size = 1
# If tracing, train 1 epoch at a time so we can snapshot parameters; otherwise, call train once
if TRACE:
    # prepare trace storage for XOR (architecture 2-2-1)
    input_size = classic_mlp.input_size
    hidden_size = classic_mlp.hidden_layers[0]
    output_size = classic_mlp.output_size

    classic_w_hidden = np.zeros((epochs, input_size, hidden_size))
    classic_w_output = np.zeros((epochs, hidden_size, output_size))
    classic_b_hidden = (
        np.zeros((epochs, 1, hidden_size)) if classic_mlp.use_bias else None
    )
    classic_b_output = (
        np.zeros((epochs, 1, output_size)) if classic_mlp.use_bias else None
    )
    mse_history_classic = []

    # Train epoch-by-epoch (important: per-layer delays are preserved across calls)
    for e in range(epochs):
        # debug first few epochs
        if e < 3:
            print(f"DEBUG before epoch {e} classic W0:\n{classic_mlp.weights[0]}")

        # step one epoch without flushing pending updates at return
        _ = classic_mlp.train(
            X_classic,
            y_classic,
            epochs=1,
            batch_size=batch_size,
            verbose=False,
            flush_on_return=False,
        )

        if e < 3:
            print(f"DEBUG after epoch {e} classic W0:\n{classic_mlp.weights[0]}")

        # snapshot weights and biases (state after internal epoch step, but before final flush)
        classic_w_hidden[e, :, :] = classic_mlp.weights[0]
        classic_w_output[e, :, :] = classic_mlp.weights[1]
        if classic_mlp.use_bias:
            classic_b_hidden[e, 0, :] = classic_mlp.biases[0][0, :]
            classic_b_output[e, 0, :] = classic_mlp.biases[1][0, :]
        # compute current MSE on classic training set
        preds = classic_mlp.predict(X_classic)
        mse_history_classic.append(np.mean((preds - y_classic) ** 2))

    mse_history_classic = np.array(mse_history_classic)
    classic_time = time.time() - start_time

else:
    mse_history_classic = classic_mlp.train(
        X_classic, y_classic, epochs=epochs, batch_size=batch_size
    )
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

# Note: mlpGraph already built above for delay-sync with Classic training
# Set seed for Concurrent Graph (uses random.uniform) - re-seed for reproducibility
random.seed(42)
# mlpGraph instance built earlier is reused here

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

# Bias copy from Classic to Graph omitted: initial biases are zero-initialized and do not need copying
# if hasattr(mlpGraph, "biasLayers") and mlpGraph.add_bias:
#    try:
#        print("Copying biases from Classic MLP to Concurrent Graph...")
#        for layer_idx, b_array in enumerate(classic_mlp.biases):
#            if b_array is None:
#                continue
#            # b_array has shape (1, n)
#            for neuron_idx in range(b_array.shape[1]):
#                bnode = mlpGraph.biasLayers[layer_idx][neuron_idx]
#                bnode.value = float(b_array[0, neuron_idx])
#    except Exception:
#        print("Warning: could not copy biases from Classic to Graph")

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
# For trace runs we skip warmup to keep initial buffer state identical between Classic and Graph
if not TRACE:
    mlpProcessor.ComputeGraph(networkLength)

# Training - exact configuration from TestingOnXOR.py
print("Training Concurrent Graph...")
fakeBatchSize = 1
epochs = 5000
numberOfIterationsInEpochs = 4
iters_per_epoch = numberOfIterationsInEpochs * fakeBatchSize
totalIterations = epochs * iters_per_epoch

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
if TRACE:
    # per-epoch incremental ComputeGraph so we can snapshot params after each epoch
    graph_time = 0.0
    mse_history_graph = []

    # Pre-allocate storage for weights/biases matching Classic shapes
    input_size = 2
    hidden_size = mlpGraph.hiddenLayerSizes[0]
    output_size = mlpGraph.numOutputs

    graph_w_hidden = np.zeros((epochs, input_size, hidden_size))
    graph_w_output = np.zeros((epochs, hidden_size, output_size))
    graph_b_hidden = np.zeros((epochs, 1, hidden_size)) if mlpGraph.add_bias else None
    graph_b_output = np.zeros((epochs, 1, output_size)) if mlpGraph.add_bias else None

    for e in range(epochs):
        t0 = time.time()
        # step one iteration at a time so we can observe when biases/weights change
        for k in range(iters_per_epoch):
            fullGraphProcessor.ComputeGraph(1)
            # debug per-iteration bias values for first epoch
            if e < 2:
                hb = (
                    [b.value for b in mlpGraph.biasLayers[0]]
                    if mlpGraph.add_bias
                    else None
                )
                ob = (
                    [b.value for b in mlpGraph.biasLayers[1]]
                    if mlpGraph.add_bias
                    else None
                )
                print(f"DEBUG graph iter e={e} k={k} bias hidden={hb} out={ob}")
        graph_time += time.time() - t0

        # snapshot weights: mlpGraph.weightLayers is list of layers
        # first layer: input->hidden shape (input_size x hidden_size)
        w0 = np.zeros((input_size, hidden_size))
        for i in range(input_size):
            for j in range(hidden_size):
                w0[i, j] = mlpGraph.weightLayers[0][i][j].value
        graph_w_hidden[e] = w0
        # output weights
        w1 = np.zeros((hidden_size, output_size))
        for i in range(hidden_size):
            for j in range(output_size):
                w1[i, j] = mlpGraph.weightLayers[1][i][j].value
        graph_w_output[e] = w1
        # biases
        if mlpGraph.add_bias:
            graph_b_hidden[e, 0, :] = [b.value for b in mlpGraph.biasLayers[0]]
            graph_b_output[e, 0, :] = [b.value for b in mlpGraph.biasLayers[1]]
        # compute MSE for this epoch using buffers (robust to None entries)
        mse = 0
        start_idx = e * iters_per_epoch
        end_idx = (e + 1) * iters_per_epoch
        for errorBuffer in errorBuffers:
            values = [v for v in errorBuffer.buffer[start_idx:end_idx] if v is not None]
            if len(values) > 0:
                mse += np.mean(np.array(values) ** 2)
            else:
                mse += 0.0
        mse = mse / len(errorBuffers)
        mse_history_graph.append(mse)

    mse_history_graph = np.array(mse_history_graph)
else:
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
    newMSEOverEpochs = MSEOverEpochs.reshape(
        -1, numberOfIterationsInEpochs * fakeBatchSize
    )
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

# If tracing, save traces to artifacts/xor_traces/ and run exact equality checks
if TRACE:
    out_dir = "artifacts/xor_traces"
    import os

    os.makedirs(out_dir, exist_ok=True)
    np.savez_compressed(
        os.path.join(out_dir, "xor_seed42_traces.npz"),
        classic_w_hidden=classic_w_hidden,
        classic_w_output=classic_w_output,
        classic_b_hidden=classic_b_hidden,
        classic_b_output=classic_b_output,
        classic_mse=np.array(mse_history_classic),
        graph_w_hidden=graph_w_hidden,
        graph_w_output=graph_w_output,
        graph_b_hidden=graph_b_hidden,
        graph_b_output=graph_b_output,
        graph_mse=np.array(mse_history_graph),
    )

    # Exact per-epoch equality check (tolerance 1e-12)
    tol = 1e-12
    equal = True
    first_diff = None
    for e in range(epochs):
        if not np.allclose(classic_w_hidden[e], graph_w_hidden[e], atol=tol, rtol=0):
            equal = False
            first_diff = ("W_xH0", e, classic_w_hidden[e], graph_w_hidden[e])
            break
        if not np.allclose(classic_w_output[e], graph_w_output[e], atol=tol, rtol=0):
            equal = False
            first_diff = ("W_H0y", e, classic_w_output[e], graph_w_output[e])
            break
        if classic_b_hidden is not None:
            if not np.allclose(
                classic_b_hidden[e], graph_b_hidden[e], atol=tol, rtol=0
            ):
                equal = False
                first_diff = ("B_H0", e, classic_b_hidden[e], graph_b_hidden[e])
                break
        if classic_b_output is not None:
            if not np.allclose(
                classic_b_output[e], graph_b_output[e], atol=tol, rtol=0
            ):
                equal = False
                first_diff = ("B_y", e, classic_b_output[e], graph_b_output[e])
                break
    if equal:
        print(
            "TRACE: All per-epoch weights and biases are exactly equal within tolerance."
        )
    else:
        name, e, cval, gval = first_diff
        print(f"TRACE: First difference at epoch {e}, param {name}.")
        print("Classic:\n", cval)
        print("Graph:\n", gval)

    # Compare first-update epoch for biases between Classic and Graph
    if classic_b_hidden is not None:
        tol = 1e-12

        def first_nonzero_epoch(arr):
            for e in range(arr.shape[0]):
                if np.any(np.abs(arr[e, 0, :]) > tol):
                    return e
            return None

        classic_hidden_epoch = first_nonzero_epoch(classic_b_hidden)
        graph_hidden_epoch = (
            first_nonzero_epoch(graph_b_hidden) if graph_b_hidden is not None else None
        )
        classic_out_epoch = (
            first_nonzero_epoch(classic_b_output)
            if classic_b_output is not None
            else None
        )
        graph_out_epoch = (
            first_nonzero_epoch(graph_b_output) if graph_b_output is not None else None
        )

        print(
            "\nTRACE TIMING CHECK: comparing Classic vs Graph bias first-update epochs"
        )
        print(
            f"Hidden bias: Classic={classic_hidden_epoch}, Graph={graph_hidden_epoch}"
        )
        print(f"Output bias: Classic={classic_out_epoch}, Graph={graph_out_epoch}")
        if (
            classic_hidden_epoch == graph_hidden_epoch
            and classic_out_epoch == graph_out_epoch
        ):
            print("TRACE TIMING CHECK: PASS — Classic bias updates align with Graph.")
        else:
            print(
                "TRACE TIMING CHECK: FAIL — Classic bias updates do not align with Graph."
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
