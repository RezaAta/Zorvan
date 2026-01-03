import numpy as np

from ClassicMLP import ClassicMLP
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.DivisionNode import DivisionNode
from ComputationalGraphs.Nodes.MaxNode import MaxNode
from ComputationalGraphs.Nodes.MinNode import MinNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
from ComputationalGraphs.Nodes.PiecewiseLinearNode import PiecewiseLinearNode
from Experiments.HybridTempPredictionComparison import (
    build_graph_mlp,
    build_hybrid_from_trained_mlp,
    closed_loop_simulation_classic,
    closed_loop_simulation_classic_detached,
    closed_loop_simulation_graph_detached,
    copy_weights_to_classic,
    fis_classic,
    generate_dataset_samples,
    run_compare_multiple,
)


def build_fis_graph(error_val, delta_val):
    """Construct a small standalone FIS graph and return the graph and output node."""
    from ComputationalGraphs.Core.Graph import Graph

    full = Graph()
    err_in = DisplayNode("ErrIn", value=error_val)
    dp_in = DisplayNode("DpIn", value=delta_val)
    full.AddNode(err_in, dp_in)

    neg = PiecewiseLinearNode(
        "Err_Neg", xs=[-10, -5, -2, 0, 2], mus=[1, 1, 0.5, 0.0, 0.0]
    )
    neg.AddPreNode(err_in)
    zero = PiecewiseLinearNode(
        "Err_Zero", xs=[-2, -1, 0, 1, 2], mus=[0.0, 0.5, 1.0, 0.5, 0.0]
    )
    zero.AddPreNode(err_in)
    pos = PiecewiseLinearNode(
        "Err_Pos", xs=[-2, 0, 2, 5, 10], mus=[0.0, 0.0, 0.5, 1.0, 1.0]
    )
    pos.AddPreNode(err_in)

    dec = PiecewiseLinearNode(
        "DT_Dec", xs=[-2.0, -1.0, -0.5, 0.0, 0.0], mus=[1, 1, 0.5, 0.0, 0.0]
    )
    dec.AddPreNode(dp_in)
    stable = PiecewiseLinearNode(
        "DT_Stable", xs=[-0.5, -0.1, 0.0, 0.1, 0.5], mus=[0.0, 0.5, 1.0, 0.5, 0.0]
    )
    stable.AddPreNode(dp_in)
    inc = PiecewiseLinearNode(
        "DT_Inc", xs=[0.0, 0.0, 0.5, 1.0, 2.0], mus=[0.0, 0.0, 0.5, 1.0, 1.0]
    )
    inc.AddPreNode(dp_in)

    full.AddNode(neg, zero, pos, dec, stable, inc)

    cons_matrix = [[0.0, 0.0, 0.0], [25.0, 50.0, 75.0], [50.0, 75.0, 100.0]]
    rules = []
    products = []
    for i, arow in enumerate([neg, zero, pos]):
        for j, acol in enumerate([dec, stable, inc]):
            r = MinNode(f"R_{i}_{j}")
            r.AddPreNode(arow, acol)
            c = DisplayNode(f"Cons_{i}_{j}", value=cons_matrix[i][j])
            p = MultiplicationNode(f"P_{i}_{j}")
            p.AddPreNode(r, c)
            full.AddNode(r, c, p)
            rules.append(r)
            products.append(p)

    numerator = AdditionNode("FIS_Num")
    numerator.AddPreNode(*products)
    denominator = AdditionNode("FIS_Den")
    denominator.AddPreNode(*rules)
    out = DivisionNode("FIS_Out")
    out.AddPreNode(numerator, denominator)
    full.AddNode(numerator, denominator, out)

    # clamp
    zero_c = DisplayNode("MinPower", 0.0)
    hundred_c = DisplayNode("MaxPower", 100.0)
    maxed = MaxNode("AtLeastZero")
    maxed.AddPreNode(out, zero_c)
    clamped = MinNode("ClampedPower")
    clamped.AddPreNode(maxed, hundred_c)
    full.AddNode(zero_c, hundred_c, maxed, clamped)

    full.starting_nodes = [err_in, dp_in]
    full.UpdateAdjacencyMatrix()
    return full, clamped


def test_fis_matches_classic():
    # test several points including edge cases
    pairs = [(-5.0, -1.0), (0.0, 0.0), (2.0, 0.5), (5.0, -0.3), (-1.5, 1.0)]
    for err, dp in pairs:
        g, out = build_fis_graph(err, dp)
        proc = GraphProcessor(g, verbose=False)
        # run enough iterations to ensure propagation and stable outputs
        proc.ComputeGraphSingleThread(50)
        g_out = out.value
        c_out = fis_classic(err, dp)
        assert (
            abs((g_out or 0.0) - c_out) < 1e-6
        ), f"Mismatch err={err}, dp={dp}, graph={g_out}, classic={c_out}"


def test_target_is_constant():
    X, y = generate_dataset_samples(50, seed=0)
    mlp, scalers = build_graph_mlp(X, y)
    hybrid = build_hybrid_from_trained_mlp(mlp, setpoint=22.0)
    # Find the target DisplayNode
    targets = [
        n for n in hybrid.nodes if isinstance(n, DisplayNode) and n.name == "TargetTemp"
    ]
    assert len(targets) == 1
    assert targets[0].value == 22.0


def test_buffer_node_updates():
    # Build small mlp and hybrid graph, then run forward and check buffer contains input
    X, y = generate_dataset_samples(80, seed=1)
    mlp, scalers = build_graph_mlp(X, y)
    hybrid = build_hybrid_from_trained_mlp(mlp, setpoint=22.0)
    # set a known input
    in0 = mlp.inputLayer[0][0]
    in1 = mlp.inputLayer[1][0]
    in0.data = [15.5]
    in0.value = 15.5
    in1.data = [0.1]
    in1.value = 0.1

    proc = GraphProcessor(hybrid, verbose=False)
    net_len = 3 * (mlp.numHiddenLayers + 1)
    proc.ComputeGraphSingleThread(max(20, net_len * 3))

    buffers = [n for n in hybrid.nodes if n.name == "Buff_x0_for_FIS"]
    assert len(buffers) == 1
    buff = buffers[0]
    # After running the graph, the buffer should contain the input value somewhere
    assert any((v == 15.5) for v in getattr(buff, "buffer", []))


def test_classic_closed_loop_matches_detached():
    # Build small dataset and untrained MLP/classic pair with identical weights
    X, y = generate_dataset_samples(80, seed=2)
    mlp, scalers = build_graph_mlp(X, y)
    classic = ClassicMLP(
        input_size=2,
        output_size=1,
        hidden_layers=[8, 8],
        hidden_activation="relu",
        output_activation="linear",
        learning_rate=0.001,
        use_bias=True,
    )
    copy_weights_to_classic(mlp, classic)

    seed = 12345
    g_temps, g_powers, g_errors = closed_loop_simulation_classic_detached(
        classic, scalers, steps=50, target=22.0, rng_seed=seed, verbose=False
    )
    c_temps, c_powers, c_errors = closed_loop_simulation_classic(
        classic, steps=50, target=22.0, rng_seed=seed, verbose=False, scalers=scalers
    )

    # Results should be identical when using the same normalization logic
    assert np.allclose(g_temps, c_temps)
    assert np.allclose(g_powers, c_powers)
    assert np.allclose(g_errors, c_errors)


def test_static_env_deterministic_by_seed_graph_and_classic():
    # Verify that with static environment defaults, runs are deterministic per-seed
    X, y = generate_dataset_samples(80, seed=4)
    mlp, scalers = build_graph_mlp(X, y)

    seed = 2025
    g1_t, g1_p, g1_e = closed_loop_simulation_graph_detached(
        mlp, scalers, steps=10, rng_seed=seed, verbose=False
    )
    g2_t, g2_p, g2_e = closed_loop_simulation_graph_detached(
        mlp, scalers, steps=10, rng_seed=seed, verbose=False
    )
    assert np.array_equal(g1_t, g2_t)

    # different seed should produce a different initial temperature
    g3_t, _, _ = closed_loop_simulation_graph_detached(
        mlp, scalers, steps=1, rng_seed=seed + 1, verbose=False
    )
    assert g1_t[0] != g3_t[0]

    # For Classic detached variant (normalized), same seed -> identical traces
    classic = ClassicMLP(
        input_size=2,
        output_size=1,
        hidden_layers=[8, 8],
        hidden_activation="relu",
        output_activation="linear",
        learning_rate=0.001,
        use_bias=True,
    )
    copy_weights_to_classic(mlp, classic)
    c1_t, c1_p, c1_e = closed_loop_simulation_classic_detached(
        classic, scalers, steps=10, rng_seed=seed, verbose=False
    )
    c2_t, c2_p, c2_e = closed_loop_simulation_classic_detached(
        classic, scalers, steps=10, rng_seed=seed, verbose=False
    )
    assert np.array_equal(c1_t, c2_t)


def test_export_per_trial_table(tmp_path):
    """Run 3 trials and export per-trial CSV + Markdown table; verify outputs."""
    csv_path = str(tmp_path / "compare_test_table.csv")
    md_path = str(tmp_path / "compare_test_table.md")

    results = run_compare_multiple(
        n_runs=3, verbose=False, save_file=None, csv_file=csv_path
    )
    assert len(results) == 3

    import csv as _csv
    import os

    assert os.path.exists(csv_path)
    with open(csv_path, newline="") as fh:
        reader = _csv.DictReader(fh)
        rows = list(reader)

    assert len(rows) == 3 + 3  # 3 trials + 3 summary rows
    expected_fields = [
        "trial",
        "master_seed",
        "shared_seed",
        "graph_final_temp",
        "graph_diff",
        "classic_final_temp",
        "classic_diff",
    ]
    assert reader.fieldnames == expected_fields

    # basic numeric sanity checks for per-trial rows
    per_rows = rows[:-3]
    for r in per_rows:
        float(r["graph_final_temp"])
        float(r["classic_final_temp"])
        float(r["graph_diff"])
        float(r["classic_diff"])

    # validate summary rows
    avg_row = rows[-3]
    diff_row = rows[-2]
    pct_row = rows[-1]

    import statistics

    avg_graph = statistics.mean(float(r["graph_final_temp"]) for r in per_rows)
    avg_classic = statistics.mean(float(r["classic_final_temp"]) for r in per_rows)

    assert avg_row["trial"] == "AVERAGE"
    assert abs(float(avg_row["graph_final_temp"]) - avg_graph) < 1e-6

    assert diff_row["trial"] == "DIFFERENCE"
    diff_expected = avg_graph - avg_classic
    assert abs(float(diff_row["graph_final_temp"]) - diff_expected) < 1e-6

    assert pct_row["trial"] == "PERCENT_DIFF"
    pct_expected = (
        (diff_expected / avg_classic) * 100.0 if avg_classic != 0 else float("inf")
    )
    assert abs(float(pct_row["graph_final_temp"]) - pct_expected) < 1e-6

    # check markdown file was created alongside csv
    assert os.path.exists(md_path)
