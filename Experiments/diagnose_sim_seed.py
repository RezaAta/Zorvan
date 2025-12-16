"""Diagnose a single simulation seed step-by-step for Graph and Classic hybrids.

Usage: adjust MASTER_SEED and SIM_SEED constants below and run.
"""

import os
import runpy

import numpy as np

# Config: reproduce the run you posted
MASTER_SEED = 1883152922
SIM_SEED = 1539516188
STEPS = 50


def load_experiment():
    path = os.path.join(os.path.dirname(__file__), "HybridTempPredictionComparison.py")
    ns = runpy.run_path(path)
    return ns


def main():
    ns = load_experiment()
    generate_dataset_samples = ns["generate_dataset_samples"]
    build_graph_mlp = ns["build_graph_mlp"]
    train_graph_mlp = ns["train_graph_mlp"]
    copy_weights_to_classic = ns["copy_weights_to_classic"]
    graph_predict_single = ns["graph_predict_single"]
    closed_loop_simulation_graph_detached = ns["closed_loop_simulation_graph_detached"]
    closed_loop_simulation_classic_detached = ns[
        "closed_loop_simulation_classic_detached"
    ]
    ClassicMLP = (
        ns["ClassicMLP"] if "ClassicMLP" in ns else __import__("ClassicMLP").ClassicMLP
    )

    print(f"Reproducing master_seed={MASTER_SEED}, sim_seed={SIM_SEED}")

    # Build data and seed RNGs deterministically
    X, y = generate_dataset_samples(1200, seed=MASTER_SEED)
    np.random.seed(MASTER_SEED)
    import random

    random.seed(MASTER_SEED)

    mlp_graph, scalers = build_graph_mlp([X[0][:800], X[1][:800]], [y[0][:800]])
    mlp_graph, full_graph, scalers = train_graph_mlp(
        [X[0][:800], X[1][:800]],
        [y[0][:800]],
        epochs=80,
        itersPerEpoch=4,
        mlp=mlp_graph,
    )

    # Classic: initialize from graph initial weights (we'll re-build fresh to ensure same start)
    classic = ClassicMLP(
        input_size=2,
        output_size=1,
        hidden_layers=[8, 8],
        hidden_activation="relu",
        output_activation="linear",
        learning_rate=0.001,
        use_bias=True,
    )
    copy_weights_to_classic(mlp_graph, classic)

    # Now run short sims with the SIM_SEED and collect per-step diagnostics
    # run baseline sims with prev_power=0.0
    g_temps, g_powers, g_errors = closed_loop_simulation_graph_detached(
        mlp_graph, scalers, steps=STEPS, target=22.0, rng_seed=SIM_SEED
    )
    c_temps, c_powers, c_errors = closed_loop_simulation_classic_detached(
        classic, scalers, steps=STEPS, target=22.0, rng_seed=SIM_SEED
    )

    print(
        "\nNow re-running Graph and Classic sims with initial_prev_power=0.5 and max_delta=1.5 to show effect:"
    )
    g_temps2, g_powers2, g_errors2 = closed_loop_simulation_graph_detached(
        mlp_graph,
        scalers,
        steps=STEPS,
        target=22.0,
        rng_seed=SIM_SEED,
        initial_prev_power=0.5,
        max_delta=1.5,
    )
    c_temps2, c_powers2, c_errors2 = closed_loop_simulation_classic_detached(
        classic,
        scalers,
        steps=STEPS,
        target=22.0,
        rng_seed=SIM_SEED,
        initial_prev_power=0.5,
        max_delta=1.5,
    )

    # Re-run but collect delta_pred per step to inspect
    # We'll reuse the simulation code in this file by reimplementing a short loop
    rng = np.random.RandomState(SIM_SEED)
    outside = rng.uniform(-10.0, 35.0)
    k_loss = rng.uniform(0.01, 0.12)
    k_heater = rng.uniform(0.05, 0.5)
    T = rng.uniform(5.0, 25.0)

    print("outside", outside, "k_loss", k_loss, "k_heater", k_heater, "initial_T", T)

    prev_power = 0.0
    print("step T err delta_pred_g delta_pred_c power_g power_c")
    for t in range(STEPS):
        T_pre = T
        delta_g = graph_predict_single(mlp_graph, T_pre, prev_power, scalers)
        # classic uses normalized input
        xn = np.array(
            [
                [
                    (T_pre - scalers["x0_mean"]) / scalers["x0_std"],
                    (prev_power - scalers["x1_mean"]) / scalers["x1_std"],
                ]
            ]
        )
        delta_c = classic.predict(xn)[0, 0] * scalers["y_std"] + scalers["y_mean"]
        err = 22.0 - T_pre
        power_g = ns["fis_classic"](err, delta_g)
        power_c = ns["fis_classic"](err, delta_c)
        print(
            f"{t} {T_pre:.6f} {err:.6f} {delta_g:.6f} {delta_c:.6f} {power_g:.3f} {power_c:.3f}"
        )
        power_norm = power_g / 100.0
        T = T + (k_heater * power_norm - k_loss * (T - outside))
        prev_power = power_norm


if __name__ == "__main__":
    main()
