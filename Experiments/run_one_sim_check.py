"""Run one quick sim to compare initial RNG T and first returned temperature."""

import os
import runpy

import numpy as np

# Import the experiment module by path to avoid package import issues
exp_path = os.path.join(os.path.dirname(__file__), "HybridTempPredictionComparison.py")
exp_ns = runpy.run_path(exp_path)
generate_dataset_samples = exp_ns["generate_dataset_samples"]
build_graph_mlp = exp_ns["build_graph_mlp"]
train_graph_mlp = exp_ns["train_graph_mlp"]
closed_loop_simulation_graph_detached = exp_ns["closed_loop_simulation_graph_detached"]


def compute_initial_T(seed):
    rng = np.random.RandomState(seed)
    _ = rng.uniform(-10.0, 35.0)
    _ = rng.uniform(0.01, 0.12)
    _ = rng.uniform(0.05, 0.5)
    return rng.uniform(5.0, 25.0)


def main():
    X, y = generate_dataset_samples(200, seed=1)
    mlp, scalers = build_graph_mlp(X, y)
    # train briefly to have a trained model but fast
    mlp, full, scalers = train_graph_mlp(X, y, epochs=2, itersPerEpoch=2, mlp=mlp)

    seed = 99
    init_T = compute_initial_T(seed)
    temps, powers, errors = closed_loop_simulation_graph_detached(
        mlp, scalers, steps=5, target=22.0, rng_seed=seed
    )
    print(f"seed={seed} initial_T={init_T:.6f} first_returned_temp={temps[0]:.6f}")


if __name__ == "__main__":
    main()
