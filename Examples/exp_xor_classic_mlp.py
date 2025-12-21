# Moved from ClassicMLPTestOnXOR.py — renamed to Examples/exp_xor_classic_mlp.py
# Purpose: interactive/demo script for training a Classic MLP on XOR (experiments/demos should live under Examples/ or Experiments/)

import time

import matplotlib.pyplot as plt
import numpy as np

from ClassicMLP import ClassicMLP

print("=" * 70)
print("Testing Classic MLP on XOR Problem")
print("=" * 70)

X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([[0], [1], [1], [0]])

# Hyperparameters
hidden_layers = [2, 2, 2]
num_hidden_layers = 1
learning_rate = 0.5
epochs = 2000

print("\nHyperparameters:")
print(f"  Hidden layers: {hidden_layers}")
print(f"  Learning rate: {learning_rate}")
print(f"  Epochs: {epochs}")
print("  Activation: Sigmoid")
print("  Batch size: 1 (SGD)")

# Initialize and train the model
print("\nBuilding Classic MLP...")
mlp = ClassicMLP(
    input_size=X.shape[1],
    output_size=1,
    num_hidden_layers=num_hidden_layers,
    # hidden_layers=hidden_layers,
    hidden_activation="sigmoid",
    output_activation="linear",  # Linear output for regression
    learning_rate=learning_rate,
    use_bias=False,
)

# Training
print("\n" + "=" * 70)
print("Training")
print("=" * 70)

start_time = time.time()
mse_history = mlp.train(X, y, epochs=epochs, batch_size=1)
training_time = time.time() - start_time

print(f"\nTraining completed in {training_time:.2f} seconds")
print(f"Epochs per second: {epochs / training_time:.2f}")
print(f"Iterations per second: {(epochs * len(X)) / training_time:.0f}")

# Testing
print("\n" + "=" * 70)
print("Testing")
print("=" * 70)

predictions = mlp.predict(X).flatten()
ground_truth = y.flatten()

for i in range(len(X)):
    prediction = predictions[i]
    actual = ground_truth[i]
    error = prediction - actual

    # Binary prediction
    binary_pred = 1 if prediction > 0.5 else 0

    print(
        f"Input: {X[i].tolist()} -> Predicted: {prediction:.4f} ({binary_pred}), Actual: {int(actual)}, Error: {error:.4f}"
    )

# Evaluate the model
mae = mlp.evaluate(X, y)
print(f"\nTest MAE: {mae:.4f}")

# Calculate accuracy
predictions_binary = [1 if p > 0.5 else 0 for p in predictions]
correct = sum(
    [1 for i in range(len(ground_truth)) if predictions_binary[i] == ground_truth[i]]
)
accuracy = correct / len(ground_truth)

print(f"Accuracy: {accuracy*100:.1f}% ({correct}/{len(ground_truth)})")

print("\n" + "=" * 70)
print("Test completed!")
print("=" * 70)

# Plot training loss
plt.figure(figsize=(10, 6))
plt.plot(range(1, epochs + 1), mse_history, linewidth=2, color="#A23B72")
plt.title("Training Loss Curve")
plt.xlabel("Epochs")
plt.ylabel("Mean Squared Error")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("xor_classic_mlp_training_curve.png", dpi=300, bbox_inches="tight")
print("\nPlot saved as 'xor_classic_mlp_training_curve.png'")
plt.show()
