"""Compare Classic MLP vs Concurrent Graph MLP on the temperature prediction task.

This script is modeled after `test_xor_classic_vs_concurrent.py` but uses
network configs and data generation from `HybridTempPredictionComparison.py`.

Plots: learning curves (linear and log) for Classic vs Graph using per-epoch MSE.
"""

import logging

# Ensure project root is on sys.path so imports like `Experiments.xxx` work when running this
# script directly from the `Experiments/` folder (Python sets sys.path[0] to the script dir).
import os
import random
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

from ClassicMLP import ClassicMLP

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from Experiments.HybridTempPredictionComparison import (
    build_graph_mlp,
    copy_weights_to_classic,
    generate_dataset_samples,
    graph_predict_single,
    train_graph_mlp_with_mse_history,
)

logger = logging.getLogger(__name__)


def run_experiment(
    n_samples=1200,
    master_seed=None,
    epochs=80,
    itersPerEpoch=4,
    learning_rate=0.001,
    verbose=True,
):
    if master_seed is None:
        master_seed = np.random.randint(0, 2**31 - 1)
    if verbose:
        logger.info("Experiment master_seed=%s", master_seed)

    # Generate dataset and split
    X, y = generate_dataset_samples(n_samples=n_samples, seed=master_seed)
    n = len(X[0])
    idx = np.arange(n)
    np.random.seed(1)
    np.random.shuffle(idx)
    train_idx = idx[: int(0.8 * n)]
    test_idx = idx[int(0.8 * n) :]

    X_train = [np.array(X[0])[train_idx].tolist(), np.array(X[1])[train_idx].tolist()]
    y_train = [np.array(y[0])[train_idx].tolist()]

    X_test = [np.array(X[0])[test_idx].tolist(), np.array(X[1])[test_idx].tolist()]
    y_test = [np.array(y[0])[test_idx].tolist()]

    # Deterministic initialization
    random.seed(master_seed)
    np.random.seed(master_seed)

    # Build untrained Graph MLP (this will also set scalers)
    mlp_graph, scalers = build_graph_mlp(X_train, y_train)

    # Initialize Classic MLP and copy initial weights from graph so they start identically
    classic = ClassicMLP(
        input_size=2,
        output_size=1,
        hidden_layers=[8, 8],
        hidden_activation="relu",
        output_activation="linear",
        learning_rate=learning_rate,
        use_bias=True,
    )
    copy_weights_to_classic(mlp_graph, classic)

    # Train Graph MLP and collect mse histories (per-iteration and per-epoch)
    start = time.time()
    mlp_graph, full_graph, scalers, graph_mse_iter, graph_mse_epoch = (
        train_graph_mlp_with_mse_history(
            X_train,
            y_train,
            epochs=epochs,
            itersPerEpoch=itersPerEpoch,
            mlp=mlp_graph,
            learning_rate=learning_rate,
        )
    )
    graph_time = time.time() - start

    # Train Classic MLP on same normalized data (full-batch per-epoch)
    Xn_raw = np.vstack([np.array(X_train[0]), np.array(X_train[1])]).T
    Xn = np.column_stack(
        [
            (Xn_raw[:, 0] - scalers["x0_mean"]) / scalers["x0_std"],
            (Xn_raw[:, 1] - scalers["x1_mean"]) / scalers["x1_std"],
        ]
    )
    yn = (np.array(y_train[0]) - scalers["y_mean"]) / scalers["y_std"]
    yn = yn.reshape(-1, 1)

    start = time.time()
    # Train for `epochs` to match graph_mse_epoch length
    classic_mse = classic.train(Xn, yn, epochs=epochs, batch_size=len(Xn))
    classic_time = time.time() - start

    # Evaluate on test set
    # Classic predictions (normalize, predict, de-normalize)
    Xn_test = np.column_stack(
        [
            (np.array(X_test[0]) - scalers["x0_mean"]) / scalers["x0_std"],
            (np.array(X_test[1]) - scalers["x1_mean"]) / scalers["x1_std"],
        ]
    )
    classic_preds = (
        classic.predict(Xn_test).flatten() * scalers["y_std"] + scalers["y_mean"]
    )

    # Graph predictions: use PrepareForTest and read prediction buffer
    mlp_graph.PrepareForTest(X_test, y_test)
    proc = GraphProcessor(mlp_graph, verbose=False)
    net_len = 3 * (len(mlp_graph.hiddenLayers) + 1)
    proc.ComputeGraph(len(X_test[0]) + net_len)
    graph_preds = (
        np.array(mlp_graph.predictionBuffers[0].buffer) * scalers["y_std"]
        + scalers["y_mean"]
    )

    y_true = np.array(y_test[0])

    # Test metrics
    classic_mse_test = float(np.mean((classic_preds - y_true) ** 2))
    graph_mse_test = float(np.mean((graph_preds - y_true) ** 2))

    classic_mae_test = float(np.mean(np.abs(classic_preds - y_true)))
    graph_mae_test = float(np.mean(np.abs(graph_preds - y_true)))

    # Print summary
    print("=" * 80)
    print("MLP Temperature Prediction: Classic vs Concurrent Graph")
    print("=" * 80)
    print(f"Training time (Classic): {classic_time:.4f}s, (Graph): {graph_time:.4f}s")
    print(f"Final train MSE (Classic): {classic_mse[-1]:.6f}")
    print(f"Final train MSE (Graph): {graph_mse_epoch[-1]:.6f}")
    print(f"Test MSE (Classic): {classic_mse_test:.6f}")
    print(f"Test MSE (Graph): {graph_mse_test:.6f}")
    print(f"Test MAE (Classic): {classic_mae_test:.6f}")
    print(f"Test MAE (Graph): {graph_mae_test:.6f}")

    # Plot learning curves (linear and log) following XOR script style
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(classic_mse, label="Classic MLP", linewidth=2, alpha=0.8, color="blue")
    axes[0].plot(
        graph_mse_epoch,
        label="Concurrent Graph",
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

    axes[1].plot(classic_mse, label="Classic MLP", linewidth=2, alpha=0.8, color="blue")
    axes[1].plot(
        graph_mse_epoch,
        label="Concurrent Graph",
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
    outname = "mlp_temp_classic_vs_concurrent.png"
    plt.savefig(outname, dpi=150, bbox_inches="tight")
    print(f"\nLearning curves saved to: {outname}")
    plt.show()

    return dict(
        classic_mse=classic_mse,
        graph_mse_epoch=graph_mse_epoch,
        graph_mse_iter=graph_mse_iter,
        classic_preds=classic_preds,
        graph_preds=graph_preds,
        y_true=y_true,
    )


if __name__ == "__main__":
    run_experiment()
