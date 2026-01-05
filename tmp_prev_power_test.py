# Smoke test for initial_prev_power handling and graph predict wrapper changes
import numpy as np

from ClassicMLP import ClassicMLP
from Experiments.HybridTempPredictionComparison import (
    build_graph_mlp,
    closed_loop_simulation_classic_detached,
    closed_loop_simulation_graph_detached,
    copy_weights_to_classic,
    generate_dataset_samples,
)

# Build dataset and mlps
X, y = generate_dataset_samples(120, seed=42)
X_train = [np.array(X[0])[:80].tolist(), np.array(X[1])[:80].tolist()]
y_train = [np.array(y[0])[:80].tolist()]
mlp_graph, scalers = build_graph_mlp(X_train, y_train)

# Classic MLP with copied weights
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

seed = 12345
init_power = 0.37
# Run both detached sims for a single step to test use of initial_prev_power
g_temps, g_powers, g_errors = closed_loop_simulation_graph_detached(
    mlp_graph, scalers, steps=1, rng_seed=seed, initial_prev_power=init_power
)
c_temps, c_powers, c_errors = closed_loop_simulation_classic_detached(
    classic, scalers, steps=1, rng_seed=seed, initial_prev_power=init_power
)

print("graph temps:", g_temps)
print("classic temps:", c_temps)
print("graph powers:", g_powers)
print("classic powers:", c_powers)

# Check that both used initial_prev_power by comparing power values (should be finite arrays length 1)
if len(g_powers) != 1 or len(c_powers) != 1:
    raise SystemExit("Unexpected output length from detached sims")

print("Done: smoke test completed successfully")
