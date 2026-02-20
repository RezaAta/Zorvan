"""
Multi-trial comparison: Classic MLP vs Concurrent MLPGraph on the Diabetes dataset.

- Runs N paired trials.
- Ensures identical initial weights & biases per trial (generated from a single numpy RNG).
- Uses concurrent processing for the graph-based MLP (with biases enabled).
- Collects per-iteration MSE histories for both approaches and plots:
  * all trials overlay (linear & log)
  * mean ± std convergence (linear & log)

Notes:
- Classic MLP records full-training-set MSE after each sample update (per-iteration).
- Graph MLP records its MeanSquaredNode value after each iteration.

"""

import os
import random
import time

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ClassicMLP import ClassicMLP
from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.SigmoidNode import SigmoidNode


def prepare_data(test_size=0.2, random_state=42):
    data = load_diabetes()
    X = data.data
    y = data.target.reshape(-1, 1)

    # Remove outliers with IQR rule
    q1 = np.percentile(y, 25, axis=0)
    q3 = np.percentile(y, 75, axis=0)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    mask = (y >= lower_bound) & (y <= upper_bound)
    X = X[mask.flatten()]
    y = y[mask.flatten()]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    scaler_X = StandardScaler()
    X_train = scaler_X.fit_transform(X_train)
    X_test = scaler_X.transform(X_test)

    return X_train, X_test, y_train, y_test


def generate_initial_weights_and_biases(
    rng, input_size, hidden_layers, output_size, use_bias=True
):
    # Build layer dimensions
    layer_dims = [input_size] + hidden_layers + [output_size]

    weights = []
    biases = []
    for i in range(len(layer_dims) - 1):
        w = rng.uniform(-1.0, 1.0, size=(layer_dims[i], layer_dims[i + 1]))
        weights.append(w)
        if use_bias:
            # Biases set to zero for deterministic experiments (no randomization)
            b = np.zeros((1, layer_dims[i + 1]))
        else:
            b = None
        biases.append(b)

    return weights, biases


def apply_weights_to_classic(classic: ClassicMLP, weights, biases):
    # deep copy to avoid accidental aliasing
    classic.weights = [w.copy() for w in weights]
    classic.biases = [b.copy() if b is not None else None for b in biases]


def apply_weights_to_graph(mlp: MLPGraph, classic: ClassicMLP):
    # Map Classic named weights to graph weight node values
    named = classic.get_named_weights()

    # Assign weight values
    for wl in mlp.weightLayers:
        for row in wl:
            for node in row:
                if node.name in named:
                    node.value = float(named[node.name])

    # Assign biases
    # classic.biases is a list of arrays for each weight layer (1 x n_out) or None
    # Map: biases[0] -> B_H0N{j}, biases[1] -> B_H1N{j}, ..., biases[last] -> B_y{j}
    for layer_idx, b in enumerate(classic.biases):
        if b is None:
            continue
        # shape: (1, n_out)
        n_out = b.shape[1]
        if layer_idx < len(mlp.biasLayers) - 1:
            # hidden layer biases
            for j in range(n_out):
                name = f"B_H{layer_idx}N{j}"
                # find and set
                for bnode in mlp.biasLayers[layer_idx]:
                    if bnode.name == name:
                        bnode.value = float(b[0, j])
        else:
            # output biases
            out_layer = len(mlp.biasLayers) - 1
            for j in range(n_out):
                name = f"B_y{j}"
                for bnode in mlp.biasLayers[out_layer]:
                    if bnode.name == name:
                        bnode.value = float(b[0, j])


def format_data_for_graph(X, y):
    # MLPGraph expects row-per-feature lists and labels as list-of-lists
    X_t = X.T.tolist()
    y_t = y.T.tolist()
    return X_t, y_t


def compare_weights_biases(classic: ClassicMLP, mlp: MLPGraph, verbose: bool = True):
    """Compare ClassicMLP weights/biases with MLPGraph ContainerNode values.

    Returns a dict with summary statistics and lists of mismatches (if any).
    """
    named = classic.get_named_weights()

    weight_diffs = []
    weight_total = 0
    weight_mismatches = []
    for wl in mlp.weightLayers:
        for row in wl:
            for node in row:
                weight_total += 1
                if node.name in named:
                    ref = float(named[node.name])
                    val = float(node.value)
                    diff = abs(val - ref)
                    pct = (diff / (abs(ref) + 1e-12)) * 100.0
                    weight_diffs.append(diff)
                    if pct > 1e-9:
                        weight_mismatches.append((node.name, ref, val, diff, pct))

    bias_diffs = []
    bias_total = 0
    bias_mismatches = []
    # classic.biases list corresponds to layers; biasLayers in mlp maps hidden layers + output
    for layer_idx, b in enumerate(classic.biases):
        if b is None:
            continue
        n_out = b.shape[1]
        bias_total += n_out
        if layer_idx < len(mlp.biasLayers) - 1:
            # hidden biases
            for j in range(n_out):
                name = f"B_H{layer_idx}N{j}"
                ref = float(b[0, j])
                # find node
                node = next(
                    (bn for bn in mlp.biasLayers[layer_idx] if bn.name == name), None
                )
                if node is None:
                    bias_mismatches.append((name, ref, None, None, None))
                    continue
                val = float(node.value)
                diff = abs(val - ref)
                pct = (diff / (abs(ref) + 1e-12)) * 100.0
                bias_diffs.append(diff)
                if pct > 1e-9:
                    bias_mismatches.append((name, ref, val, diff, pct))
        else:
            # output biases
            out_layer = len(mlp.biasLayers) - 1
            for j in range(n_out):
                name = f"B_y{j}"
                ref = float(b[0, j])
                node = next(
                    (bn for bn in mlp.biasLayers[out_layer] if bn.name == name), None
                )
                if node is None:
                    bias_mismatches.append((name, ref, None, None, None))
                    continue
                val = float(node.value)
                diff = abs(val - ref)
                pct = (diff / (abs(ref) + 1e-12)) * 100.0
                bias_diffs.append(diff)
                if pct > 1e-9:
                    bias_mismatches.append((name, ref, val, diff, pct))

    summary = {
        "weight_total": weight_total,
        "weight_mismatches": len(weight_mismatches),
        "weight_max_abs_diff": float(max(weight_diffs)) if weight_diffs else 0.0,
        "weight_max_pct_diff": (
            float(max((n[4] for n in weight_mismatches))) if weight_mismatches else 0.0
        ),
        "bias_total": bias_total,
        "bias_mismatches": len(bias_mismatches),
        "bias_max_abs_diff": float(max(bias_diffs)) if bias_diffs else 0.0,
        "bias_max_pct_diff": (
            float(max((b[4] for b in bias_mismatches))) if bias_mismatches else 0.0
        ),
        "weight_mismatch_examples": weight_mismatches[:5],
        "bias_mismatch_examples": bias_mismatches[:5],
    }

    if verbose:
        print("\nWeight/bias comparison summary:")
        print(
            f"  Weight nodes: {summary['weight_total']}, mismatches: {summary['weight_mismatches']}, max abs diff: {summary['weight_max_abs_diff']:.6e}, max % diff: {summary['weight_max_pct_diff']:.6f}%"
        )
        print(
            f"  Bias nodes:   {summary['bias_total']}, mismatches: {summary['bias_mismatches']}, max abs diff: {summary['bias_max_abs_diff']:.6e}, max % diff: {summary['bias_max_pct_diff']:.6f}%"
        )
        if summary["weight_mismatch_examples"]:
            print("  Weight examples (name, ref, val, absdiff, %):")
            for ex in summary["weight_mismatch_examples"]:
                print(f"    {ex}")
        if summary["bias_mismatch_examples"]:
            print("  Bias examples (name, ref, val, absdiff, %):")
            for ex in summary["bias_mismatch_examples"]:
                print(f"    {ex}")

    return summary


def run_single_trial(
    seed,
    X_train,
    y_train,
    hidden_layers,
    learning_rate,
    epochs,
    batch_size=1,
    use_bias=True,
    shuffle=True,
    X_test=None,
    y_test=None,
):
    rng = np.random.RandomState(seed)

    n_features = X_train.shape[1]
    n_samples = X_train.shape[0]

    # Generate initial weights/biases
    weights, biases = generate_initial_weights_and_biases(
        rng, n_features, hidden_layers, 1, use_bias=use_bias
    )

    # === Classic MLP setup ===
    classic = ClassicMLP(
        input_size=n_features,
        output_size=1,
        hidden_layers=hidden_layers,
        learning_rate=learning_rate,
        use_bias=use_bias,
    )
    apply_weights_to_classic(classic, weights, biases)

    # === Graph MLP setup (concurrent mode) ===
    mlp_graph = MLPGraph(
        numInputs=n_features,
        numOutputs=1,
        numHiddenLayers=len(hidden_layers),
        hiddenLayerSizes=hidden_layers,
        activationFunction=SigmoidNode,
        outputLayerType=LinearNode,
        add_bias=use_bias,
        use_bias=use_bias,
    )
    mlp_graph.BuildMLP()

    # Assign identical weights/biases to graph nodes
    apply_weights_to_graph(mlp_graph, classic)

    # Compare immediately after copying to ensure identical initialization
    init_cmp = compare_weights_biases(classic, mlp_graph, verbose=True)

    # Build backprop and graph structures
    backprop = BackpropGraph(mlp_graph, learningRate=learning_rate)
    backprop.BuildBackprop()

    graph = Graph()
    for node in mlp_graph.nodes:
        graph.AddNode(node)
    for node in backprop.nodes:
        graph.AddNode(node)

    # Force single-threaded execution for deterministic timing and reproducibility
    processor = GraphProcessor(graph, max_workers=1, verbose=False)

    # Prepare data for graph
    X_t, y_t = format_data_for_graph(X_train, y_train)
    mlp_graph.LoadData(X_t, y_t)

    # Prepare error buffers and MSE nodes for monitoring
    total_iterations = epochs * n_samples * batch_size
    mlp_graph.CreateErrorBuffers(total_iterations, mse_buffer_size=n_samples)

    # Set MeanSquaredNode mode to 'batch' so .value only updates when its buffer is full
    # and reset buffers so batch counting starts from zero
    for ms in getattr(mlp_graph, "mseNodes", []):
        try:
            ms.mode = "batch"
            ms.ResetBuffer()
        except Exception:
            pass

    # Add buffers and mse nodes to graph (if not already added by CreateErrorBuffers)
    for eb in getattr(mlp_graph, "errorBuffers", []):
        if eb not in graph.nodes:
            graph.AddNode(eb)
    for ms in getattr(mlp_graph, "mseNodes", []):
        if ms not in graph.nodes:
            graph.AddNode(ms)

    # Warmup
    networkLength = 3 * (mlp_graph.numHiddenLayers + 1)
    processor.ComputeGraphSingleThread(networkLength)

    # === Training ===
    # Classic: per-sample updates, record full-training MSE after each update
    classic_mse_history = []
    start_c = time.perf_counter()
    for ep in range(epochs):
        # Optionally shuffle per epoch for SGD behaviour
        idxs = list(range(n_samples))
        if shuffle:
            random.shuffle(idxs)
        for i in idxs:
            X_batch = X_train[i : i + 1]
            y_batch = y_train[i : i + 1]
            acts = classic.forward_pass(X_batch)
            classic.backward_pass(X_batch, y_batch, acts)

            # Compute full-training-set MSE (for consistent per-iteration recording)
            preds = classic.predict(X_train)
            mse = float(np.mean((preds - y_train) ** 2))
            classic_mse_history.append(mse)
    classic_time = time.perf_counter() - start_c

    # Graph: run all iterations (single-threaded for deterministic timing)
    start_g = time.perf_counter()
    processor.ComputeGraphSingleThread(total_iterations)
    graph_time = time.perf_counter() - start_g

    # Extract per-iteration MSE from error buffers (square instantaneous errors and average across outputs)
    graph_mse_history = []
    for i in range(total_iterations):
        mse = 0.0
        for errorBuffer in mlp_graph.errorBuffers:
            mse += (errorBuffer.buffer[i]) ** 2
        mse = mse / len(mlp_graph.errorBuffers)
        graph_mse_history.append(float(mse))

    # Print times
    print(
        f"Trial seed={seed} — Classic time: {classic_time:.3f}s, Graph time: {graph_time:.3f}s"
    )

    # Sanity: lengths
    if len(classic_mse_history) != len(graph_mse_history):
        print(
            f"Warning: history lengths differ: classic={len(classic_mse_history)}, graph={len(graph_mse_history)}"
        )

    # Convert per-iteration MSE histories to per-epoch MSE (match exp_testing_on_diabetes.py)
    per_epoch_size = batch_size * n_samples
    try:
        classic_epochs = (
            np.array(classic_mse_history)
            .reshape(epochs, per_epoch_size)
            .mean(axis=1)
            .tolist()
        )
    except Exception:
        # Fallback: if reshape fails, compute epoch means manually
        classic_epochs = []
        for e in range(epochs):
            start = e * per_epoch_size
            end = start + per_epoch_size
            classic_epochs.append(float(np.mean(classic_mse_history[start:end])))

    try:
        graph_epochs = (
            np.array(graph_mse_history)
            .reshape(epochs, per_epoch_size)
            .mean(axis=1)
            .tolist()
        )
    except Exception:
        graph_epochs = []
        for e in range(epochs):
            start = e * per_epoch_size
            end = start + per_epoch_size
            graph_epochs.append(float(np.mean(graph_mse_history[start:end])))

    # Compute test MAE for both models if test data provided
    classic_mae = None
    graph_mae = None
    if X_test is not None and y_test is not None:
        # Classic MAE
        preds_classic = classic.predict(X_test)
        classic_mae = float(np.mean(np.abs(preds_classic - y_test)))

        # Graph MAE: Prepare test and run forward processing on mlp_graph only
        X_t_test, y_t_test = format_data_for_graph(X_test, y_test)
        mlp_graph.PrepareForTest(X_t_test, y_t_test)
        mlp_test_processor = GraphProcessor(mlp_graph, max_workers=1, verbose=False)
        testing_epochs = len(X_t_test[0]) + networkLength
        mlp_test_processor.ComputeGraphSingleThread(testing_epochs)

        # Collect predictions
        predictionValues = []
        for pb in getattr(mlp_graph, "predictionBuffers", []):
            predictionValues.extend(pb.buffer)
        predictionValues = np.array(predictionValues)
        graph_mae = float(
            np.mean(np.abs(np.array(y_test).flatten() - predictionValues.flatten()))
        )

    # Also compare weights/biases after training to see how training diverged
    post_cmp = compare_weights_biases(classic, mlp_graph, verbose=True)

    return classic_epochs, graph_epochs, classic_mae, graph_mae, init_cmp, post_cmp


def pad_histories(histories):
    """Pad histories to same length and forward-fill NaN/None values.

    - Missing early MSE samples may be NaN (we append NaN when MeanSquaredNode
      hasn't produced a batch value yet). This function forward-fills NaNs and
      replaces fully-NaN series with zeros to avoid plot breaks.
    """
    max_len = max(len(h) for h in histories)
    padded = []
    for h in histories:
        # Make a mutable copy and extend to max length by repeating last value
        h2 = list(h)
        if len(h2) < max_len:
            if len(h2) == 0:
                h2 = [np.nan] * max_len
            else:
                h2 = h2 + [h2[-1]] * (max_len - len(h2))

        # Normalize None to np.nan
        h2 = [np.nan if (x is None) else x for x in h2]

        # Forward-fill NaNs where possible
        last_val = np.nan
        for i in range(len(h2)):
            if isinstance(h2[i], float) and np.isnan(h2[i]):
                # replace with last valid if available
                h2[i] = (
                    last_val
                    if not (isinstance(last_val, float) and np.isnan(last_val))
                    else np.nan
                )
            else:
                last_val = h2[i]

        # If still all NaN, fill with zeros. Otherwise replace leading NaNs with first valid
        if all(isinstance(x, float) and np.isnan(x) for x in h2):
            h2 = [0.0] * len(h2)
        else:
            # find first valid value
            first_valid = None
            for val in h2:
                if not (isinstance(val, float) and np.isnan(val)):
                    first_valid = val
                    break
            h2 = [
                first_valid if (isinstance(x, float) and np.isnan(x)) else x for x in h2
            ]

        padded.append(h2)

    return np.array(padded)


def plot_results(classic_histories, graph_histories, out_prefix, num_trials):
    # Pad
    classic_p = pad_histories(classic_histories)
    graph_p = pad_histories(graph_histories)

    classic_mean = np.mean(classic_p, axis=0)
    classic_std = np.std(classic_p, axis=0)
    graph_mean = np.mean(graph_p, axis=0)
    graph_std = np.std(graph_p, axis=0)

    # Mean ± Std (LOG)
    plt.figure(figsize=(10, 6))
    x = range(1, len(classic_mean) + 1)
    plt.plot(x, classic_mean, label="Classic (mean)")
    plt.fill_between(
        x, classic_mean - classic_std, classic_mean + classic_std, alpha=0.3
    )
    plt.plot(x, graph_mean, label="Graph (mean)")
    plt.fill_between(x, graph_mean - graph_std, graph_mean + graph_std, alpha=0.3)
    plt.yscale("log")
    plt.xlabel("Iteration")
    plt.ylabel("MSE")
    plt.title(f"Mean ± Std MSE (Log Scale) — {num_trials} trials")
    plt.legend()
    plt.grid(True, which="both")
    fname = f"{out_prefix}_mean_std_log_{num_trials}trials.png"
    plt.tight_layout()
    plt.savefig(fname, dpi=150)
    print(f"Saved {fname}")

    # Mean ± Std (Linear)
    plt.figure(figsize=(10, 6))
    plt.plot(x, classic_mean, label="Classic (mean)")
    plt.fill_between(
        x, classic_mean - classic_std, classic_mean + classic_std, alpha=0.3
    )
    plt.plot(x, graph_mean, label="Graph (mean)")
    plt.fill_between(x, graph_mean - graph_std, graph_mean + graph_std, alpha=0.3)
    plt.xlabel("Iteration")
    plt.ylabel("MSE")
    plt.title(f"Mean ± Std MSE (Linear Scale) — {num_trials} trials")
    plt.legend()
    plt.grid(True)
    fname = f"{out_prefix}_mean_std_linear_{num_trials}trials.png"
    plt.tight_layout()
    plt.savefig(fname, dpi=150)
    print(f"Saved {fname}")

    # All trials overlay - LOG and LINEAR
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    for h in classic_histories:
        ax1.plot(range(1, len(h) + 1), h, color="blue", alpha=0.4)
    ax1.plot(range(1, len(classic_mean) + 1), classic_mean, color="k", linewidth=2)
    ax1.set_yscale("log")
    ax1.set_title("Classic — All trials (Log)")
    ax1.grid(True, which="both")

    for h in graph_histories:
        ax2.plot(range(1, len(h) + 1), h, color="green", alpha=0.4)
    ax2.plot(range(1, len(graph_mean) + 1), graph_mean, color="k", linewidth=2)
    ax2.set_yscale("log")
    ax2.set_title("Graph — All trials (Log)")
    ax2.grid(True, which="both")

    fname = f"{out_prefix}_all_trials_log_{num_trials}trials.png"
    plt.tight_layout()
    plt.savefig(fname, dpi=150)
    print(f"Saved {fname}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    for h in classic_histories:
        ax1.plot(range(1, len(h) + 1), h, color="blue", alpha=0.4)
    ax1.plot(range(1, len(classic_mean) + 1), classic_mean, color="k", linewidth=2)
    ax1.set_title("Classic — All trials (Linear)")
    ax1.grid(True)

    for h in graph_histories:
        ax2.plot(range(1, len(h) + 1), h, color="green", alpha=0.4)
    ax2.plot(range(1, len(graph_mean) + 1), graph_mean, color="k", linewidth=2)
    ax2.set_title("Graph — All trials (Linear)")
    ax2.grid(True)

    fname = f"{out_prefix}_all_trials_linear_{num_trials}trials.png"
    plt.tight_layout()
    plt.savefig(fname, dpi=150)
    print(f"Saved {fname}")


def main():
    out_dir = os.getcwd()

    # Experiment configuration
    num_trials = 10
    hidden_layers = [10]
    learning_rate = 0.0001
    epochs = 100  # Set to 100 epochs per your request
    batch_size = 1
    use_bias = True

    X_train, X_test, y_train, y_test = prepare_data()

    n_samples = X_train.shape[0]
    expected_iterations_per_trial = epochs * n_samples * batch_size
    print(
        f"Experiment configuration: hidden_layers={hidden_layers}, learning_rate={learning_rate}, epochs={epochs}, batch_size={batch_size}"
    )
    print(
        f"Expected iterations per trial (graph iterations): {expected_iterations_per_trial}"
    )

    classic_histories = []
    graph_histories = []

    # Randomize base seed for the experiment and report it for reproducibility
    base_seed = int(np.random.randint(0, 2**31 - 1))
    print(f"Base seed: {base_seed}")

    mae_classic_list = []
    mae_graph_list = []
    seeds = []

    for trial in range(1, num_trials + 1):
        seed = base_seed + trial
        print(f"\n=== Trial {trial}/{num_trials} — seed={seed} ===")
        c_hist, g_hist, c_mae, g_mae, init_cmp, post_cmp = run_single_trial(
            seed,
            X_train,
            y_train,
            hidden_layers,
            learning_rate,
            epochs,
            batch_size=batch_size,
            use_bias=use_bias,
            shuffle=False,  # Disable shuffling in Classic to match Graph ordering
            X_test=X_test,
            y_test=y_test,
        )
        classic_histories.append(c_hist)
        graph_histories.append(g_hist)
        mae_classic_list.append(c_mae)
        mae_graph_list.append(g_mae)
        seeds.append(seed)

        # Print init/post comparison summaries
        print(
            f"\nInit comparison (trial {trial}): Weight mismatches={init_cmp['weight_mismatches']}, Bias mismatches={init_cmp['bias_mismatches']}"
        )
        print(
            f"Post-training comparison (trial {trial}): Weight mismatches={post_cmp['weight_mismatches']}, Bias mismatches={post_cmp['bias_mismatches']}"
        )

    out_prefix = os.path.join(out_dir, f"diabetes_compare_{num_trials}trials")
    plot_results(classic_histories, graph_histories, out_prefix, num_trials)

    # Build MAE table and save as CSV + print formatted table
    import csv

    csv_fname = f"{out_prefix}_mae_table_{num_trials}trials.csv"
    with open(csv_fname, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Trial",
                "Seed",
                "Classic MAE",
                "Graph MAE",
                "Difference (Graph-Classic)",
                "Diff %",
            ]
        )
        for i in range(num_trials):
            c = mae_classic_list[i]
            g = mae_graph_list[i]
            s = seeds[i]
            diff = None if (c is None or g is None) else (g - c)
            diff_pct = (
                None if (c is None or g is None or c == 0) else (diff / c * 100.0)
            )
            writer.writerow(
                [
                    i + 1,
                    s,
                    f"{c:.6f}",
                    f"{g:.6f}",
                    f"{diff:.6f}" if diff is not None else "",
                    f"{diff_pct:.2f}%" if diff_pct is not None else "",
                ]
            )

        # mean row
        c_mean = float(np.mean([x for x in mae_classic_list if x is not None]))
        g_mean = float(np.mean([x for x in mae_graph_list if x is not None]))
        diff_mean = g_mean - c_mean
        diff_mean_pct = (diff_mean / c_mean * 100.0) if c_mean != 0 else float("nan")
        writer.writerow([])
        writer.writerow(
            [
                "MEAN",
                "",
                f"{c_mean:.6f}",
                f"{g_mean:.6f}",
                f"{diff_mean:.6f}",
                f"{diff_mean_pct:.2f}%",
            ]
        )

    print(f"\nMAE table saved as: {csv_fname}")

    # Print table nicely
    header = f"{'Trial':<6}{'Seed':<12}{'Classic MAE':<16}{'Graph MAE':<16}{'Difference':<16}{'Diff %':<10}"
    print("\n" + header)
    print("-" * len(header))
    for i in range(num_trials):
        c = mae_classic_list[i]
        g = mae_graph_list[i]
        s = seeds[i]
        diff = g - c
        diff_pct = (diff / c * 100.0) if c != 0 else float("nan")
        print(f"{i+1:<6}{s:<12}{c:<16.6f}{g:<16.6f}{diff:<16.6f}{diff_pct:<10.2f}")

    print("\nSummary:")
    print(f"MEAN: Classic={c_mean:.6f}, Graph={g_mean:.6f}")
    print(f"DIFF: {diff_mean:.6f} ({diff_mean_pct:.2f}%)")

    print(f"\nDone. Plots + MAE table written to {out_dir}")


if __name__ == "__main__":
    main()
