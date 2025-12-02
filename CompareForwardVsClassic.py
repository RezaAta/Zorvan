"""
Controlled comparison: Forward Processing vs Classic MLP
Both start with IDENTICAL weights to ensure fair comparison.
"""

import time

import matplotlib.pyplot as plt
import numpy as np

from ClassicMLP import ClassicMLP
from ComputationalGraphs.Core.BackpropGraphForwardProcessing import (
    BackpropGraphForwardProcessing,
)
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode

print("=" * 70)
print("CONTROLLED COMPARISON: Forward Processing vs Classic MLP")
print("Both implementations start with IDENTICAL weights")
print("=" * 70)

# XOR dataset
X_train = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
y_train = [[0.0], [1.0], [1.0], [0.0]]

X_classic = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y_classic = np.array([[0], [1], [1], [0]])

# Hyperparameters
hidden_layers = [4]
learning_rate = 0.5
epochs = 100

# Set fixed random seed for reproducibility
np.random.seed(42)

print(f"\nHyperparameters:")
print(f"  Hidden layers: {hidden_layers}")
print(f"  Learning rate: {learning_rate}")
print(f"  Epochs: {epochs}")
print(f"  Random seed: 42")

# ============================================================================
# BUILD FORWARD PROCESSING MLP
# ============================================================================
print("\n" + "=" * 70)
print("Building Forward Processing MLP...")
print("=" * 70)

mlp_forward = MLPGraphForwardProcessing(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    hiddenLayerSizes=hidden_layers,
    activationFunction=SigmoidNode,
)
mlp_forward.BuildMLP()

backprop_forward = BackpropGraphForwardProcessing(
    mlp_forward, learningRate=learning_rate
)
backprop_forward.BuildBackprop()

fullGraph = Graph()
for node in mlp_forward.nodes:
    fullGraph.AddNode(node)
for node in backprop_forward.nodes:
    fullGraph.AddNode(node)

# Set starting nodes (first-layer multiplications + learning rate)
fullGraph.starting_nodes = mlp_forward.starting_nodes + [backprop_forward.lrNode]
fullGraph.UpdateAdjacencyMatrix()

processor_forward = GraphProcessor(fullGraph, verbose=False)

print(f"Built: {len(fullGraph.nodes)} nodes")

# ============================================================================
# BUILD CLASSIC MLP
# ============================================================================
print("\n" + "=" * 70)
print("Building Classic MLP...")
print("=" * 70)

mlp_classic = ClassicMLP(
    input_size=2,
    output_size=1,
    hidden_layers=hidden_layers,
    hidden_activation="sigmoid",
    output_activation="linear",  # Linear output to match Forward Processing
    learning_rate=learning_rate,
    use_bias=False,
)

print(f"Built: {len(mlp_classic.weights)} weight matrices")

# ============================================================================
# EXTRACT INITIAL WEIGHTS FROM FORWARD PROCESSING
# ============================================================================
print("\n" + "=" * 70)
print("Extracting initial weights from Forward Processing MLP...")
print("=" * 70)

# Get weight nodes from forward processing MLP
weight_nodes = [node for node in mlp_forward.nodes if node.name.startswith("W_")]

# Group weights by layer
input_to_hidden_weights = []
hidden_to_output_weights = []

for node in weight_nodes:
    if "x0" in node.name or "x1" in node.name:
        # Input to hidden layer weights
        input_to_hidden_weights.append((node.name, node.value))
    elif "H0N" in node.name and "y0" in node.name:
        # Hidden to output layer weights
        hidden_to_output_weights.append((node.name, node.value))

print(f"\nForward Processing initial weights:")
print(f"  Input->Hidden: {len(input_to_hidden_weights)} weights")
for name, val in sorted(input_to_hidden_weights):
    print(f"    {name}: {val:.6f}")

print(f"  Hidden->Output: {len(hidden_to_output_weights)} weights")
for name, val in sorted(hidden_to_output_weights):
    print(f"    {name}: {val:.6f}")

# ============================================================================
# SET CLASSIC MLP TO USE SAME INITIAL WEIGHTS
# ============================================================================
print("\n" + "=" * 70)
print("Setting Classic MLP to use SAME initial weights...")
print("=" * 70)

# Construct weight matrices matching the computational graph structure
# Forward processing structure: W_x0H0N0, W_x0H0N1, W_x0H0N2, W_x0H0N3
#                                W_x1H0N0, W_x1H0N1, W_x1H0N2, W_x1H0N3
# Classic structure: weights[0] = [2, 4] matrix (2 inputs, 4 hidden)
#                    weights[1] = [4, 1] matrix (4 hidden, 1 output)

# Extract weights in correct order
W_input_hidden = np.zeros((2, 4))  # [inputs, hidden]
for name, val in input_to_hidden_weights:
    if "x0" in name:
        input_idx = 0
    elif "x1" in name:
        input_idx = 1

    # Extract hidden neuron index from name like "W_x0H0N2"
    hidden_idx = int(name.split("N")[1])
    W_input_hidden[input_idx, hidden_idx] = val

W_hidden_output = np.zeros((4, 1))  # [hidden, outputs]
for name, val in hidden_to_output_weights:
    # Extract hidden neuron index from name like "W_H0N2y0"
    hidden_idx = int(name.split("N")[1].split("y")[0])
    W_hidden_output[hidden_idx, 0] = val

# Set weights in classic MLP
mlp_classic.weights[0] = W_input_hidden.copy()
mlp_classic.weights[1] = W_hidden_output.copy()

print(f"\nClassic MLP weights set:")
print(f"  Input->Hidden shape: {mlp_classic.weights[0].shape}")
print(f"    {mlp_classic.weights[0]}")
print(f"  Hidden->Output shape: {mlp_classic.weights[1].shape}")
print(f"    {mlp_classic.weights[1]}")

# Verify they match
print("\n[OK] Weights verification:")
print(f"  Input->Hidden match: {np.allclose(W_input_hidden, mlp_classic.weights[0])}")
print(f"  Hidden->Output match: {np.allclose(W_hidden_output, mlp_classic.weights[1])}")

# ============================================================================
# TRAINING: FORWARD PROCESSING
# ============================================================================
print("\n" + "=" * 70)
print("Training Forward Processing MLP...")
print("=" * 70)

# Load complete dataset (match GUI example - all samples at once)
X_train_list = [[float(x) for x in sample] for sample in X_train]
y_train_list = [
    [float(y[0])] for y in y_train
]  # y_train already has nested structure [[0], [1], ...]
mlp_forward.LoadData(X_train_list, y_train_list)

# Calculate iterations needed (matching TestingForwardProcessingOnXOR.py approach)
iterations_per_sample = mlp_forward.GetPassLength()
num_samples = len(X_train)
iterations_per_epoch = iterations_per_sample * num_samples

print(f"\nForward Processing iteration calculation:")
print(f"  Iterations per sample: {iterations_per_sample}")
print(f"  Samples per epoch: {num_samples}")
print(f"  Iterations per epoch: {iterations_per_epoch}")

mse_history_forward = []
start_time = time.time()

# Training - DataStreamNodes automatically cycle through samples (no PrepareForForwardProcessing needed)
for epoch in range(epochs):
    # Run one epoch worth of iterations
    processor_forward.ForwardProcessing(iterations=iterations_per_epoch)

    # After epoch, calculate MSE from error nodes
    errors_squared = []
    for error_node in mlp_forward.errorLayer:
        if error_node.value is not None:
            errors_squared.append(error_node.value**2)

    if errors_squared:
        epoch_mse = np.mean(errors_squared)
    else:
        epoch_mse = 0.0

    mse_history_forward.append(epoch_mse)

    if epoch == 0 or (epoch + 1) % 10 == 0 or epoch == epochs - 1:
        print(f"Epoch {epoch+1}/{epochs}, MSE: {epoch_mse:.6f}")

training_time_forward = time.time() - start_time
print(f"\nTraining completed in {training_time_forward:.2f} seconds")

# ============================================================================
# TRAINING: CLASSIC MLP
# ============================================================================
print("\n" + "=" * 70)
print("Training Classic MLP...")
print("=" * 70)

start_time = time.time()

# Manually implement training loop to match forward processing exactly
mse_history_classic = []

for epoch in range(epochs):
    epoch_mse = 0.0

    for sample_idx in range(len(X_classic)):
        # Get single sample
        X_sample = X_classic[sample_idx : sample_idx + 1]
        y_sample = y_classic[sample_idx : sample_idx + 1]

        # Forward pass
        activations = mlp_classic.forward_pass(X_sample)

        # Backward pass (updates weights)
        mlp_classic.backward_pass(X_sample, y_sample, activations)

        # Calculate MSE for this sample
        mse = np.mean((activations[-1] - y_sample) ** 2)
        epoch_mse += mse

    epoch_mse /= len(X_classic)
    mse_history_classic.append(epoch_mse)

    if epoch == 0 or (epoch + 1) % 10 == 0 or epoch == epochs - 1:
        print(f"Epoch {epoch+1}/{epochs}, MSE: {epoch_mse:.6f}")

training_time_classic = time.time() - start_time
print(f"\nTraining completed in {training_time_classic:.2f} seconds")

# ============================================================================
# TESTING: FORWARD PROCESSING
# ============================================================================
print("\n" + "=" * 70)
print("Testing Forward Processing MLP...")
print("=" * 70)

# Run inference on all test samples
predictions_forward = []
print("Testing on all samples:")
for i in range(len(X_train)):
    # Load single sample
    X_single = [X_train[i]]
    y_single = [y_train[i]]
    mlp_forward.LoadData(X_single, y_single)

    # Run forward pass only (enough iterations for signal propagation)
    # For 2-4-1 network: input layer (2 iters) + hidden layer (4 iters) + output (2 iters) ~ 20 total
    processor_forward.ForwardProcessing(
        iterations=20, starting_nodes=mlp_forward.starting_nodes
    )

    # Read output from activation node
    prediction = mlp_forward.outputLayer[0][1].value
    binary_pred = 1 if prediction > 0.5 else 0
    actual = y_train[i][0]
    print(
        f"Input: {X_train[i]} -> Predicted: {prediction:.4f} ({binary_pred}), Actual: {int(actual)}"
    )
    predictions_forward.append(prediction)

mae_forward = np.mean(
    [abs(predictions_forward[i] - y_train[i][0]) for i in range(len(y_train))]
)
print(f"\nTest MAE: {mae_forward:.4f}")

# ============================================================================
# TESTING: CLASSIC MLP
# ============================================================================
print("\n" + "=" * 70)
print("Testing Classic MLP...")
print("=" * 70)

predictions_classic = mlp_classic.predict(X_classic).flatten()

for i in range(len(X_classic)):
    prediction = predictions_classic[i]
    binary_pred = 1 if prediction > 0.5 else 0
    actual = y_classic[i][0]
    print(
        f"Input: {X_classic[i].tolist()} -> Predicted: {prediction:.4f} ({binary_pred}), Actual: {int(actual)}"
    )

mae_classic = mlp_classic.evaluate(X_classic, y_classic)
print(f"\nTest MAE: {mae_classic:.4f}")

# ============================================================================
# COMPARISON
# ============================================================================
print("\n" + "=" * 70)
print("COMPARISON RESULTS")
print("=" * 70)

print(f"\nFinal MSE:")
print(f"  Forward Processing: {mse_history_forward[-1]:.6f}")
print(f"  Classic MLP:        {mse_history_classic[-1]:.6f}")
print(
    f"  Difference:         {abs(mse_history_forward[-1] - mse_history_classic[-1]):.6f}"
)

print(f"\nTest MAE:")
print(f"  Forward Processing: {mae_forward:.6f}")
print(f"  Classic MLP:        {mae_classic:.6f}")
print(f"  Difference:         {abs(mae_forward - mae_classic):.6f}")

print(f"\nTraining Time:")
print(f"  Forward Processing: {training_time_forward:.4f}s")
print(f"  Classic MLP:        {training_time_classic:.4f}s")
print(f"  Speedup:            {training_time_forward / training_time_classic:.2f}x")

# Check if results are equivalent
mse_close = np.allclose(
    mse_history_forward[-1], mse_history_classic[-1], rtol=1e-3, atol=1e-3
)
mae_close = np.allclose(mae_forward, mae_classic, rtol=1e-3, atol=1e-3)

print(f"\n{'='*70}")
if mse_close and mae_close:
    print("[OK] RESULTS MATCH: Forward Processing behaves identically to Classic MLP")
    print("  (within numerical precision tolerance)")
else:
    print("[ERROR] RESULTS DIFFER: Implementations do not match!")
    print("  This indicates a bug or algorithmic difference.")
print(f"{'='*70}")

# ============================================================================
# PLOT COMPARISON
# ============================================================================
plt.figure(figsize=(14, 5))

# Plot 1: MSE Comparison
plt.subplot(1, 2, 1)
plt.plot(
    range(1, epochs + 1),
    mse_history_forward,
    label="Forward Processing",
    linewidth=2,
    color="#2A9D8F",
)
plt.plot(
    range(1, epochs + 1),
    mse_history_classic,
    label="Classic MLP",
    linewidth=2,
    color="#E63946",
    linestyle="--",
    alpha=0.8,
)
plt.xlabel("Epoch")
plt.ylabel("Mean Squared Error")
plt.title("Training MSE Comparison (Identical Initial Weights)")
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 2: MSE Difference Over Time
plt.subplot(1, 2, 2)
mse_diff = [abs(mse_history_forward[i] - mse_history_classic[i]) for i in range(epochs)]
plt.plot(range(1, epochs + 1), mse_diff, linewidth=2, color="#264653")
plt.xlabel("Epoch")
plt.ylabel("Absolute MSE Difference")
plt.title("MSE Difference: |Forward - Classic|")
plt.yscale("log")
plt.grid(True, alpha=0.3, which="both")

plt.tight_layout()
plt.savefig(
    "forward_vs_classic_controlled_comparison.png", dpi=300, bbox_inches="tight"
)
print("\nPlot saved as 'forward_vs_classic_controlled_comparison.png'")
plt.show()
