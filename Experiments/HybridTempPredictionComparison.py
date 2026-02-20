"""Compare concurrent Graph-based hybrid controller with a Classic MLP + FIS replica.

Steps:
- Generate training dataset (random episodes / samples)
- Train Graph MLP (concurrent MLPGraph + BackpropGraph)
- Train Classic MLP (`ClassicMLP`) with same architecture
- Build hybrid controller graph from trained `mlpGraph` (attach FIS)
- Run closed-loop evaluation on held-out episodes for both controllers
- Print comparison metrics and plot a single episode
"""

import csv
import logging
import math
import time

import matplotlib.pyplot as plt
import numpy as np

from ClassicMLP import ClassicMLP
from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.AdditionNode import AdditionNode
from zorvan.Nodes.DisplayNode import DisplayNode
from zorvan.Nodes.DisplayNode import DisplayNode as DNode
from zorvan.Nodes.DivisionNode import DivisionNode
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.MaxNode import MaxNode
from zorvan.Nodes.MinNode import MinNode
from zorvan.Nodes.MultiplicationNode import MultiplicationNode
from zorvan.Nodes.PiecewiseLinearNode import PiecewiseLinearNode
from zorvan.Nodes.ReLUNode import ReLUNode
from zorvan.Nodes.SubtractionNode import SubtractionNode

logger = logging.getLogger(__name__)


def generate_dataset_samples(n_samples=1000, seed=42, k_loss=0.03, k_heater=0.3):
    """Generate training samples with fixed physical parameters.

    Args:
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        k_loss: Heat loss coefficient (constant)
        k_heater: Heater gain coefficient (constant)
    """
    rng = np.random.RandomState(seed)
    dt = 1.0
    current_temps = rng.uniform(5.0, 30.0, size=n_samples)
    prev_powers = rng.uniform(0.0, 1.0, size=n_samples)
    outside = rng.uniform(-10.0, 35.0, size=n_samples)
    delta_T = dt * (k_heater * prev_powers - k_loss * (current_temps - outside))
    X = [current_temps.tolist(), prev_powers.tolist()]
    y = [delta_T.tolist()]
    return X, y


def build_graph_mlp(X, y):
    """Build an MLPGraph and return it untrained along with scalers."""
    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=2,
        hiddenLayerSizes=[8, 8],
        activationFunction=ReLUNode,
        outputLayerType=LinearNode,
    )
    # Normalize inputs and outputs (standard score) to stabilize training
    import numpy as _np

    X0 = _np.array(X[0])
    X1 = _np.array(X[1])
    y0 = _np.array(y[0])
    x0_mean, x0_std = X0.mean(), X0.std() or 1.0
    x1_mean, x1_std = X1.mean(), X1.std() or 1.0
    y_mean, y_std = y0.mean(), y0.std() or 1.0

    Xn0 = ((X0 - x0_mean) / x0_std).tolist()
    Xn1 = ((X1 - x1_mean) / x1_std).tolist()
    yn0 = (((y0 - y_mean) / y_std)).tolist()

    mlp.BuildMLP()
    mlp.LoadData([Xn0, Xn1], [yn0])
    scalers = dict(
        x0_mean=x0_mean,
        x0_std=x0_std,
        x1_mean=x1_mean,
        x1_std=x1_std,
        y_mean=y_mean,
        y_std=y_std,
    )
    return mlp, scalers


def train_graph_mlp(X, y, epochs=80, itersPerEpoch=4, mlp=None):
    """Train an existing `mlp` or build-and-train a new one; returns trained mlp, full graph and scalers."""
    import numpy as _np

    if mlp is None:
        mlp, scalers = build_graph_mlp(X, y)
    else:
        # infer scalers from provided data
        X0 = _np.array(X[0])
        X1 = _np.array(X[1])
        y0 = _np.array(y[0])
        scalers = dict(
            x0_mean=X0.mean(),
            x0_std=X0.std() or 1.0,
            x1_mean=X1.mean(),
            x1_std=X1.std() or 1.0,
            y_mean=y0.mean(),
            y_std=y0.std() or 1.0,
        )
        Xn0 = ((X0 - scalers["x0_mean"]) / scalers["x0_std"]).tolist()
        Xn1 = ((X1 - scalers["x1_mean"]) / scalers["x1_std"]).tolist()
        yn0 = (((y0 - scalers["y_mean"]) / scalers["y_std"])).tolist()
        mlp.LoadData([Xn0, Xn1], [yn0])

    # Use smaller LR to avoid instability
    backprop = BackpropGraph(mlp, learningRate=0.001)
    backprop.BuildBackprop()

    from zorvan.Core.Graph import Graph

    full = Graph()
    for node in mlp.nodes:
        full.AddNode(node)
    for node in backprop.nodes:
        full.AddNode(node)
    mlp.CreateErrorBuffers(bufferSize=200, mse_buffer_size=len(X[0]))
    for eb in mlp.errorBuffers:
        if eb not in full.nodes:
            full.AddNode(eb)
    for mse in mlp.mseNodes:
        if mse not in full.nodes:
            full.AddNode(mse)

    full.starting_nodes = [inp[0] for inp in mlp.inputLayer] + mlp.labelLayer
    full.UpdateAdjacencyMatrix()

    totalIterations = epochs * itersPerEpoch
    mlp.CreateErrorBuffers(bufferSize=totalIterations, mse_buffer_size=itersPerEpoch)
    for eb in mlp.errorBuffers:
        if eb not in full.nodes:
            full.AddNode(eb)

    proc = GraphProcessor(full, verbose=False)
    proc.ComputeGraph(totalIterations + 1)
    return mlp, full, scalers


def train_graph_mlp_with_mse_history(
    X, y, epochs=80, itersPerEpoch=4, mlp=None, learning_rate=0.001
):
    """Train an MLPGraph and return per-iteration and per-epoch MSE history.

    This function builds the full graph with BackpropGraph using the provided
    `learning_rate`, executes training (fills error buffers), and then computes
    MSE per-iteration using the error buffers (matching XOR experiment).

    Returns: (mlp, full, scalers, mse_iter, mse_epoch)
    """
    import numpy as _np

    # Build or prepare mlp and scalers
    if mlp is None:
        mlp, scalers = build_graph_mlp(X, y)
    else:
        # infer scalers from provided data
        X0 = _np.array(X[0])
        X1 = _np.array(X[1])
        y0 = _np.array(y[0])
        scalers = dict(
            x0_mean=X0.mean(),
            x0_std=X0.std() or 1.0,
            x1_mean=X1.mean(),
            x1_std=X1.std() or 1.0,
            y_mean=y0.mean(),
            y_std=y0.std() or 1.0,
        )
        Xn0 = ((X0 - scalers["x0_mean"]) / scalers["x0_std"]).tolist()
        Xn1 = ((X1 - scalers["x1_mean"]) / scalers["x1_std"]).tolist()
        yn0 = (((y0 - scalers["y_mean"]) / scalers["y_std"])).tolist()
        mlp.LoadData([Xn0, Xn1], [yn0])

    # Build Backprop with requested learning rate
    backprop = BackpropGraph(mlp, learningRate=learning_rate)
    backprop.BuildBackprop()

    from zorvan.Core.Graph import Graph

    full = Graph()
    for node in mlp.nodes:
        full.AddNode(node)
    for node in backprop.nodes:
        full.AddNode(node)

    # Create error buffers and MSE nodes for tracking
    totalIterations = epochs * itersPerEpoch
    mlp.CreateErrorBuffers(bufferSize=totalIterations, mse_buffer_size=itersPerEpoch)
    for eb in mlp.errorBuffers:
        if eb not in full.nodes:
            full.AddNode(eb)
    for mse in mlp.mseNodes:
        if mse not in full.nodes:
            full.AddNode(mse)

    full.starting_nodes = [inp[0] for inp in mlp.inputLayer] + mlp.labelLayer
    full.UpdateAdjacencyMatrix()

    proc = GraphProcessor(full, verbose=False)
    proc.ComputeGraph(totalIterations + 1)

    # Compute MSE per-iteration from error buffers (square and average across outputs)
    mse_iter = []
    if getattr(mlp, "errorBuffers", None):
        for i in range(totalIterations):
            mse_val = 0.0
            for eb in mlp.errorBuffers:
                mse_val += (eb.buffer[i]) ** 2
            mse_val /= len(mlp.errorBuffers)
            mse_iter.append(float(mse_val))
    else:
        # fallback
        mse_iter = [float(m.value) for m in getattr(mlp, "mseNodes", [])]
        if len(mse_iter) == 1:
            mse_iter = mse_iter * totalIterations
        mse_iter = mse_iter[:totalIterations]

    # Aggregate into per-epoch MSE
    mse_epoch = []
    for e in range(epochs):
        start = e * itersPerEpoch
        end = start + itersPerEpoch
        chunk = mse_iter[start:end]
        if len(chunk) == 0:
            mse_epoch.append(float(0.0))
        else:
            mse_epoch.append(float(_np.mean(chunk)))

    return mlp, full, scalers, mse_iter, mse_epoch


def build_hybrid_from_trained_mlp(mlpGraph, setpoint=22.0):
    # Build a Graph that uses the trained mlpGraph nodes and attaches FIS
    from zorvan.Core.Graph import Graph
    from zorvan.Nodes import (
        AdditionNode,
        BufferNode,
        DisplayNode,
        DivisionNode,
        MaxNode,
        MinNode,
        MultiplicationNode,
        PiecewiseLinearNode,
        SubtractionNode,
    )

    full = Graph()
    for node in mlpGraph.nodes:
        full.AddNode(node)

    # Add MLP error buffers and mse nodes if present
    for eb in getattr(mlpGraph, "errorBuffers", []):
        if eb not in full.nodes:
            full.AddNode(eb)
    for mse in getattr(mlpGraph, "mseNodes", []):
        if mse not in full.nodes:
            full.AddNode(mse)

    # Target
    target = DisplayNode("TargetTemp", value=setpoint)
    full.AddNode(target)

    # Error
    # Create a dedicated buffer (forward pass length) to align current_temp with MLP output
    forward_length = 3 * (mlpGraph.numHiddenLayers + 1)
    current_temp_buffer = BufferNode("Buff_x0_for_FIS", size=forward_length)
    current_temp_buffer.AddPreNode(mlpGraph.inputLayer[0][0])
    full.AddNode(current_temp_buffer)
    error_node = SubtractionNode("Error")
    error_node.AddPreNode(target, current_temp_buffer)
    full.AddNode(error_node)

    # Prediction node (MLP output is already delayed by network buffers)
    delta_pred_node = mlpGraph.outputLayer[0][1]

    # Memberships
    neg = PiecewiseLinearNode(
        "Err_Neg", xs=[-10, -5, -2, 0, 2], mus=[1, 1, 0.5, 0.0, 0.0]
    )
    neg.AddPreNode(error_node)
    zero = PiecewiseLinearNode(
        "Err_Zero", xs=[-2, -1, 0, 1, 2], mus=[0.0, 0.5, 1.0, 0.5, 0.0]
    )
    zero.AddPreNode(error_node)
    pos = PiecewiseLinearNode(
        "Err_Pos", xs=[-2, 0, 2, 5, 10], mus=[0.0, 0.0, 0.5, 1.0, 1.0]
    )
    pos.AddPreNode(error_node)

    dec = PiecewiseLinearNode(
        "DT_Dec", xs=[-2.0, -1.0, -0.5, 0.0, 0.0], mus=[1, 1, 0.5, 0.0, 0.0]
    )
    dec.AddPreNode(delta_pred_node)
    stable = PiecewiseLinearNode(
        "DT_Stable", xs=[-0.5, -0.1, 0.0, 0.1, 0.5], mus=[0.0, 0.5, 1.0, 0.5, 0.0]
    )
    stable.AddPreNode(delta_pred_node)
    inc = PiecewiseLinearNode(
        "DT_Inc", xs=[0.0, 0.0, 0.5, 1.0, 2.0], mus=[0.0, 0.0, 0.5, 1.0, 1.0]
    )
    inc.AddPreNode(delta_pred_node)

    full.AddNode(neg, zero, pos, dec, stable, inc)

    # Rules and consequents
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

    # Clamp
    zero_c = DNode("MinPower", 0.0)
    hundred_c = DNode("MaxPower", 100.0)
    maxed = MaxNode("AtLeastZero")
    maxed.AddPreNode(out, zero_c)
    clamped = MinNode("ClampedPower")
    clamped.AddPreNode(maxed, hundred_c)
    full.AddNode(zero_c, hundred_c, maxed, clamped)

    # Starting nodes
    full.starting_nodes = (
        [inp[0] for inp in mlpGraph.inputLayer] + mlpGraph.labelLayer + [target]
    )
    if hasattr(mlpGraph, "stopping_nodes"):
        full.stopping_nodes = list(mlpGraph.stopping_nodes)

    full.UpdateAdjacencyMatrix()
    full._mlp_graph = mlpGraph
    full._fis_output = clamped
    return full


def copy_weights_to_classic(mlp_graph, classic):
    """Copy weights and biases from a trained `mlp_graph` into a `ClassicMLP` instance."""
    # copy weights
    for layer_idx, weightLayer in enumerate(mlp_graph.weightLayers):
        rows = len(weightLayer)
        cols = len(weightLayer[0])
        W = classic.weights[layer_idx]
        for i in range(rows):
            for j in range(cols):
                W[i, j] = weightLayer[i][j].value
    # copy biases if present
    if getattr(mlp_graph, "biasLayers", None) and classic.use_bias:
        for b_idx, biasRow in enumerate(mlp_graph.biasLayers):
            for j, bnode in enumerate(biasRow):
                classic.biases[b_idx][0, j] = bnode.value


def copy_weights_from_classic(classic, mlp_graph):
    """Copy weights and biases from a trained `ClassicMLP` into a `mlp_graph` instance.

    This is the inverse of `copy_weights_to_classic`. It mutates the graph's
    `weightLayers` and `biasLayers` in-place.
    """
    # copy weights
    for layer_idx, Wmat in enumerate(classic.weights):
        rows, cols = Wmat.shape
        weightLayer = mlp_graph.weightLayers[layer_idx]
        for i in range(rows):
            for j in range(cols):
                weightLayer[i][j].value = float(Wmat[i, j])
    # copy biases if present
    if getattr(mlp_graph, "biasLayers", None) and classic.use_bias:
        for b_idx, biasRow in enumerate(mlp_graph.biasLayers):
            for j, bnode in enumerate(biasRow):
                bnode.value = float(classic.biases[b_idx][0, j])


def fis_classic(error, delta_pred):
    # membership functions (triangle/trapezoid) matching graph's PiecewiseLinearNode
    def piecewise(x, xs, mus):
        # linear interpolation between points
        xs = np.array(xs)
        mus = np.array(mus)
        if x <= xs[0]:
            return mus[0]
        for i in range(len(xs) - 1):
            if xs[i] <= x <= xs[i + 1]:
                if xs[i] == xs[i + 1]:
                    return max(mus[i], mus[i + 1])
                t = (x - xs[i]) / (xs[i + 1] - xs[i])
                return mus[i] + t * (mus[i + 1] - mus[i])
        return mus[-1]

    # Error MFs
    neg = piecewise(error, [-10, -5, -2, 0, 2], [1, 1, 0.5, 0.0, 0.0])
    zero = piecewise(error, [-2, -1, 0, 1, 2], [0.0, 0.5, 1.0, 0.5, 0.0])
    pos = piecewise(error, [-2, 0, 2, 5, 10], [0.0, 0.0, 0.5, 1.0, 1.0])
    # delta MFs
    dec = piecewise(delta_pred, [-2.0, -1.0, -0.5, 0.0, 0.0], [1, 1, 0.5, 0.0, 0.0])
    stable = piecewise(
        delta_pred, [-0.5, -0.1, 0.0, 0.1, 0.5], [0.0, 0.5, 1.0, 0.5, 0.0]
    )
    inc = piecewise(delta_pred, [0.0, 0.0, 0.5, 1.0, 2.0], [0.0, 0.0, 0.5, 1.0, 1.0])

    # consequents
    cons = np.array([[0.0, 0.0, 0.0], [25.0, 50.0, 75.0], [50.0, 75.0, 100.0]])
    antecedent_rows = [neg, zero, pos]
    antecedent_cols = [dec, stable, inc]
    num = 0.0
    den = 0.0
    for i, arow in enumerate(antecedent_rows):
        for j, acol in enumerate(antecedent_cols):
            w = min(arow, acol)
            num += w * cons[i, j]
            den += w
    if den <= 0:
        return 0.0
    out = num / den
    return max(0.0, min(100.0, out))


def graph_predict_single(mlp_graph, x_temp, x_prev, scalers):
    """Stateless single-sample prediction using a graph MLP; returns denormalized scalar."""
    # Prepare the graph for test-time use: this detaches any backprop predecessors
    # from bias nodes and mounts prediction buffers so the network behaves as a pure
    # forward-pass MLP during single-sample predictions.
    try:
        mlp_graph.PrepareForTest(xTest=[[x_temp], [x_prev]], yTest=[[0.0]])
    except Exception:
        # PrepareForTest is safe to ignore if not available for some reason
        pass

    mlp_graph.FlushNetwork()
    mlp_graph.ResetWeightInputs()
    proc = GraphProcessor(mlp_graph, verbose=False)
    net_len = 3 * (len(mlp_graph.hiddenLayers) + 1)
    x0 = (x_temp - scalers["x0_mean"]) / scalers["x0_std"]
    x1 = (x_prev - scalers["x1_mean"]) / scalers["x1_std"]
    in0 = mlp_graph.inputLayer[0][0]
    in1 = mlp_graph.inputLayer[1][0]
    in0.data = [x0]
    in0.value = x0
    in0.streamIndex = 0
    in0.iteration = 0
    in1.data = [x1]
    in1.value = x1
    in1.streamIndex = 0
    in1.iteration = 0
    for lab in mlp_graph.labelLayer:
        lab.data = [0.0]
        lab.value = 0.0
        lab.streamIndex = 0
        lab.iteration = 0
    proc.ComputeGraphSingleThread(net_len)
    y_norm = mlp_graph.outputLayer[0][1].value
    return y_norm * scalers["y_std"] + scalers["y_mean"]


def closed_loop_simulation_graph_detached(
    mlp_graph,
    scalers,
    steps=200,
    target=22.0,
    rng_seed=None,
    verbose=False,
    initial_prev_power=None,
    max_delta=None,
):
    """Closed-loop sim that treats MLP and FIS as detached: use MLP prediction then run FIS (classic) on recorded current temp."""
    # episode parameters (deterministic with seed)
    # Allow a random seed when rng_seed is None for non-deterministic experiments
    if rng_seed is None:
        rng_seed = np.random.randint(0, 2**31 - 1)
    rng = np.random.RandomState(rng_seed)
    outside = None
    k_loss = None
    k_heater = None

    randomize_env = False

    # environment params: by default static values that allow heating to be feasible
    if randomize_env:
        outside = rng.uniform(-10.0, 35.0) if outside is None else outside
        k_loss = rng.uniform(0.01, 0.12) if k_loss is None else k_loss
        k_heater = rng.uniform(0.05, 0.5) if k_heater is None else k_heater
    else:
        outside = 15.0 if outside is None else outside
        k_loss = 0.03 if k_loss is None else k_loss
        k_heater = 0.3 if k_heater is None else k_heater

    # initialize
    T = rng.uniform(5.0, 25.0)
    if verbose:
        logger.debug("[Graph Detached] rng_seed=%s, initial_T=%.6f", rng_seed, T)
    # Allow caller to set a non-zero initial previous power to avoid large initial
    # temperature drops when outside is very cold.
    prev_power = 0.0 if initial_prev_power is None else initial_prev_power
    temps = []
    powers = []
    errors = []

    # ensure stateless per-step prediction
    def predict_graph(mlp_graph, T_in, prev_power_in):
        return graph_predict_single(mlp_graph, T_in, prev_power_in, scalers)

    for t in range(steps):
        T_pre = T  # record current temperature before prediction
        delta_pred = predict_graph(mlp_graph, T_pre, prev_power)
        err = target - T_pre
        power = fis_classic(err, delta_pred)
        power_norm = power / 100.0
        delta = k_heater * power_norm - k_loss * (T - outside)
        if max_delta is not None:
            # clamp the temperature change per step to avoid extreme jumps
            delta = max(-max_delta, min(max_delta, delta))
        T = T + delta
        prev_power = power_norm
        temps.append(T)
        powers.append(power)
        errors.append(err)

    return np.array(temps), np.array(powers), np.array(errors)


def closed_loop_simulation_classic_detached(
    classic_mlp,
    scalers,
    steps=200,
    target=22.0,
    rng_seed=None,
    verbose=False,
    initial_prev_power=None,
    max_delta=None,
):
    if rng_seed is None:
        rng_seed = np.random.randint(0, 2**31 - 1)
    rng = np.random.RandomState(rng_seed)
    outside = None
    k_loss = None
    k_heater = None

    randomize_env = False

    # environment params: by default static values that allow heating to be feasible
    if randomize_env:
        outside = rng.uniform(-10.0, 35.0) if outside is None else outside
        k_loss = rng.uniform(0.01, 0.12) if k_loss is None else k_loss
        k_heater = rng.uniform(0.05, 0.5) if k_heater is None else k_heater
    else:
        outside = 15.0 if outside is None else outside
        k_loss = 0.03 if k_loss is None else k_loss
        k_heater = 0.3 if k_heater is None else k_heater

    T = rng.uniform(5.0, 25.0)
    if verbose:
        logger.debug("[Classic Detached] rng_seed=%s, initial_T=%.6f", rng_seed, T)
    prev_power = 0.0 if initial_prev_power is None else initial_prev_power
    temps = []
    powers = []
    errors = []

    for t in range(steps):
        T_pre = T
        # normalize inputs for classic
        xn = np.array(
            [
                [
                    (T_pre - scalers["x0_mean"]) / scalers["x0_std"],
                    (prev_power - scalers["x1_mean"]) / scalers["x1_std"],
                ]
            ]
        )
        delta_pred = (
            classic_mlp.predict(xn)[0, 0] * scalers["y_std"] + scalers["y_mean"]
        )
        err = target - T_pre
        power = fis_classic(err, delta_pred)
        power_norm = power / 100.0
        delta = k_heater * power_norm - k_loss * (T - outside)
        if max_delta is not None:
            delta = max(-max_delta, min(max_delta, delta))
        T = T + delta
        prev_power = power_norm
        temps.append(T)
        powers.append(power)
        errors.append(err)

    return np.array(temps), np.array(powers), np.array(errors)


def closed_loop_simulation_classic(
    classic_mlp,
    steps=200,
    target=22.0,
    rng_seed=None,
    verbose=False,
    scalers=None,
    initial_prev_power=None,
    max_delta=None,
):
    """Closed-loop simulation for Classic MLP.

    If `scalers` is provided, inputs will be normalized before prediction and
    outputs denormalized (matching training). When `scalers` is None the
    function preserves the historical behavior (raw inputs).
    """
    if rng_seed is None:
        rng_seed = np.random.randint(0, 2**31 - 1)
    rng = np.random.RandomState(rng_seed)
    outside = None
    k_loss = None
    k_heater = None

    randomize_env = False

    # environment params: by default static values that allow heating to be feasible
    if randomize_env:
        outside = rng.uniform(-10.0, 35.0) if outside is None else outside
        k_loss = rng.uniform(0.01, 0.12) if k_loss is None else k_loss
        k_heater = rng.uniform(0.05, 0.5) if k_heater is None else k_heater
    else:
        outside = 15.0 if outside is None else outside
        k_loss = 0.03 if k_loss is None else k_loss
        k_heater = 0.3 if k_heater is None else k_heater

    T = rng.uniform(5.0, 25.0)
    if verbose:
        logger.debug("[Classic] rng_seed=%s, initial_T=%.6f", rng_seed, T)
    prev_power = 0.0 if initial_prev_power is None else initial_prev_power
    temps = []
    powers = []
    errors = []

    for t in range(steps):
        x = np.array([[T, prev_power]])
        # If scalers are given, normalize inputs and denormalize the output
        if scalers is not None:
            xn = np.array(
                [
                    [
                        (T - scalers["x0_mean"]) / scalers["x0_std"],
                        (prev_power - scalers["x1_mean"]) / scalers["x1_std"],
                    ]
                ]
            )
            delta_pred = (
                classic_mlp.predict(xn)[0, 0] * scalers["y_std"] + scalers["y_mean"]
            )
        else:
            delta_pred = classic_mlp.predict(x)[0, 0]
        err = target - T
        power = fis_classic(err, delta_pred)
        power_norm = power / 100.0
        T = T + (k_heater * power_norm - k_loss * (T - outside))
        prev_power = power_norm
        temps.append(T)
        powers.append(power)
        errors.append(err)

    return np.array(temps), np.array(powers), np.array(errors)


def run_compare():
    # generate data
    master_seed = np.random.randint(0, 2**31 - 1)
    logger.debug("Experiment master_seed=%s", master_seed)
    X, y = generate_dataset_samples(1200, seed=master_seed)
    # split train/test
    n = len(X[0])
    idx = np.arange(n)
    # NOTE: preserve ordering (no shuffle) for deterministic, repeatable experiments
    # If random splits are desired, replace with a seeded shuffle here.
    train_idx = idx[: int(0.8 * n)]
    test_idx = idx[int(0.8 * n) :]

    X_train = [np.array(X[0])[train_idx].tolist(), np.array(X[1])[train_idx].tolist()]
    y_train = [np.array(y[0])[train_idx].tolist()]

    X_test = [np.array(X[0])[test_idx].tolist(), np.array(X[1])[test_idx].tolist()]
    y_test = [np.array(y[0])[test_idx].tolist()]

    import random

    # Ensure deterministic initial weights by seeding Python's RNG and numpy
    random.seed(master_seed)
    np.random.seed(master_seed)

    # Build an untrained graph MLP to capture initial weights
    mlp_graph, scalers = build_graph_mlp(X_train, y_train)

    # Initialize Classic MLP with the graph's starting weights so both start identically
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
    # Legacy delay synchronization removed: ClassicMLP now updates weights/biases immediately (no delay API).

    # Verify initial weight copy is exact (should be zero diff)
    for layer_idx, weightLayer in enumerate(mlp_graph.weightLayers):
        W_expected = np.zeros_like(classic.weights[layer_idx])
        rows = len(weightLayer)
        cols = len(weightLayer[0])
        for i in range(rows):
            for j in range(cols):
                W_expected[i, j] = weightLayer[i][j].value
        diff_init = np.max(np.abs(W_expected - classic.weights[layer_idx]))
        logger.debug(
            "Initial copy - Layer %s max weight diff: %s", layer_idx, diff_init
        )

    # Check biases initial copy (if present)
    if getattr(mlp_graph, "biasLayers", None) and classic.use_bias:
        for b_idx, biasRow in enumerate(mlp_graph.biasLayers):
            bvals = np.array([b.value for b in biasRow])
            cb = classic.biases[b_idx][0]
            b_diff_init = np.max(np.abs(bvals - cb))
            logger.debug(
                "Initial copy - Layer %s max bias diff: %s", b_idx, b_diff_init
            )

    # Now train both from the same starting point
    mlp_graph, full_graph, scalers = train_graph_mlp(
        X_train, y_train, epochs=80, itersPerEpoch=4, mlp=mlp_graph
    )

    # Classic training on same normalized data
    Xn_raw = np.vstack([np.array(X_train[0]), np.array(X_train[1])]).T
    Xn = np.column_stack(
        [
            (Xn_raw[:, 0] - scalers["x0_mean"]) / scalers["x0_std"],
            (Xn_raw[:, 1] - scalers["x1_mean"]) / scalers["x1_std"],
        ]
    )
    yn = (np.array(y_train[0]) - scalers["y_mean"]) / scalers["y_std"]
    yn = yn.reshape(-1, 1)
    # Train for 320 epochs with full batch (960 samples) to match Graph's 320 iterations
    classic.train(Xn, yn, epochs=320, batch_size=len(Xn), verbose=False)

    # build hybrid graph from trained mlp (graph's trained weights + FIS)
    hybrid_graph = build_hybrid_from_trained_mlp(mlp_graph, setpoint=22.0)

    # Note: do NOT overwrite the `classic` weights with the trained graph weights here.
    # We want to compare the separately-trained Classic MLP vs the Graph MLP.

    # Debug: print bias values from mlp_graph
    for idx, biasRow in enumerate(mlp_graph.biasLayers):
        vals = [b.value for b in biasRow]
        logger.debug(
            "mlp_graph bias layer %s min %.6e max %.6e", idx, min(vals), max(vals)
        )

    # Post-training equality checks (these compare the trained Graph vs trained Classic)
    for layer_idx, weightLayer in enumerate(mlp_graph.weightLayers):
        W_expected = np.zeros_like(classic.weights[layer_idx])
        rows = len(weightLayer)
        cols = len(weightLayer[0])
        for i in range(rows):
            for j in range(cols):
                W_expected[i, j] = weightLayer[i][j].value
        diff = np.max(np.abs(W_expected - classic.weights[layer_idx]))
        logger.debug(
            "Post-training Layer %s max weight diff (Graph vs Classic): %s",
            layer_idx,
            diff,
        )

    # Build a fresh ClassicMLP and copy graph weights into it, then verify parity
    classic_copy = ClassicMLP(
        input_size=2,
        output_size=1,
        hidden_layers=[8, 8],
        hidden_activation="relu",
        output_activation="linear",
        learning_rate=0.001,
        use_bias=True,
    )
    copy_weights_to_classic(mlp_graph, classic_copy)

    # Verify biases copied into classic_copy (post-training copy parity)
    if getattr(mlp_graph, "biasLayers", None) and classic_copy.use_bias:
        for b_idx, biasRow in enumerate(mlp_graph.biasLayers):
            bvals = np.array([b.value for b in biasRow])
            cb = classic_copy.biases[b_idx][0]
            b_diff = np.max(np.abs(bvals - cb))
            logger.debug(
                "Post-training copy - Layer %s max bias diff: %s", b_idx, b_diff
            )

    # Verify predictions align on a small test subset (normalized appropriately)
    Xtest_pair = list(zip(X_test[0][:50], X_test[1][:50]))
    diffs = []
    for xt, xp in Xtest_pair:
        gpred = graph_predict_single(mlp_graph, xt, xp, scalers)
        xn = np.array(
            [
                [
                    (xt - scalers["x0_mean"]) / scalers["x0_std"],
                    (xp - scalers["x1_mean"]) / scalers["x1_std"],
                ]
            ]
        )
        ccopy_pred = (
            classic_copy.predict(xn)[0, 0] * scalers["y_std"] + scalers["y_mean"]
        )
        diffs.append(abs(gpred - ccopy_pred))
    logger.debug(
        "Max abs diff between graph MLP and Classic(copy) after weight copy: %.6f",
        max(diffs),
    )

    # compare predictions on a subset
    Xtest_pair = list(zip(X_test[0][:50], X_test[1][:50]))
    diffs = []
    g_preds = []
    c_preds = []
    for xt, xp in Xtest_pair:
        gpred = graph_predict_single(mlp_graph, xt, xp, scalers)
        # For classic, normalize inputs before predict (weights copied from normalized graph)
        xn = np.array(
            [
                [
                    (xt - scalers["x0_mean"]) / scalers["x0_std"],
                    (xp - scalers["x1_mean"]) / scalers["x1_std"],
                ]
            ]
        )
        activations = classic.forward_pass(xn)
        cpred = activations[-1][0, 0] * scalers["y_std"] + scalers["y_mean"]
        g_preds.append(gpred)
        c_preds.append(cpred)
        diffs.append(abs(gpred - cpred))
        # Print first mismatch for debugging
        if abs(gpred - cpred) > 1e-3:
            logger.debug("Debug sample xt=%.4f, xp=%.4f", xt, xp)
            logger.debug("graph pred: %s", gpred)
            logger.debug("classic pred: %s", cpred)
            for li, a in enumerate(activations):
                logger.debug(
                    "layer %s activation shape %s min %.6f max %.6f",
                    li,
                    a.shape,
                    float(a.min()),
                    float(a.max()),
                )
            # Additional diagnostic: manual forward using graph-extracted weights/biases
            xtn = (xt - scalers["x0_mean"]) / scalers["x0_std"]
            xpn = (xp - scalers["x1_mean"]) / scalers["x1_std"]
            xvec = np.array([[xtn, xpn]])
            W_mats = []
            B_vecs = []
            for layer_idx, weightLayer in enumerate(mlp_graph.weightLayers):
                rows = len(weightLayer)
                cols = len(weightLayer[0])
                W = np.zeros((rows, cols))
                for i in range(rows):
                    for j in range(cols):
                        W[i, j] = weightLayer[i][j].value
                W_mats.append(W)
            for b_idx, biasRow in enumerate(mlp_graph.biasLayers):
                B_vecs.append(np.array([b.value for b in biasRow]).reshape(1, -1))
            # manual forward
            h = xvec
            man_acts = [h]
            for i in range(len(W_mats)):
                h = h.dot(W_mats[i]) + B_vecs[i]
                if i < len(W_mats) - 1:
                    # ReLU
                    h = np.maximum(0.0, h)
                man_acts.append(h)
            logger.debug("Manual forward activations shapes:")
            for li, a in enumerate(man_acts):
                logger.debug(
                    "manual layer %s shape %s min %.6f max %.6f",
                    li,
                    a.shape,
                    float(a.min()),
                    float(a.max()),
                )
            break
    maxdiff = max(diffs)
    logger.debug(
        "Max abs diff between graph MLP and ClassicMLP after weight copy: %.6f", maxdiff
    )
    logger.debug(
        "Graph preds min/max/mean: %.6e/%.6e/%.6e",
        min(g_preds),
        max(g_preds),
        np.mean(g_preds),
    )
    logger.debug(
        "Classic preds min/max/mean: %.6e/%.6e/%.6e",
        min(c_preds),
        max(c_preds),
        np.mean(c_preds),
    )
    if maxdiff > 1e-6:
        logger.warning(
            "MLP outputs differ — check weight/bias mapping or numeric stability"
        )

    # run detached closed-loop evaluation for one representative episode (MLP->FIS detached)
    # Use a shared, random seed for fair comparison between Graph and Classic sims
    shared_seed = np.random.randint(0, 2**31 - 1)
    g_temps, g_powers, g_errors = closed_loop_simulation_graph_detached(
        mlp_graph, scalers, steps=200, target=22.0, rng_seed=shared_seed, verbose=True
    )
    c_temps, c_powers, c_errors = closed_loop_simulation_classic_detached(
        classic, scalers, steps=200, target=22.0, rng_seed=shared_seed, verbose=True
    )

    # compute metrics
    def metrics(errors, powers):
        final_abs_error = np.abs(errors[-10:]).mean()
        energy = np.sum(np.array(powers) / 100.0)
        overshoot = np.max(-np.minimum(errors, 0.0))
        return final_abs_error, energy, overshoot

    gm, ge, go = metrics(g_errors, g_powers)
    cm, ce, co = metrics(c_errors, c_powers)

    logger.info(
        "Graph Hybrid -> final_abs_error=%.3f, energy=%.3f, overshoot=%.3f",
        gm,
        ge,
        go,
    )
    logger.info(
        "Classic Hybrid -> final_abs_error=%.3f, energy=%.3f, overshoot=%.3f",
        cm,
        ce,
        co,
    )

    # simple comparison metric between the two closed-loop temperature traces
    temp_rmse = np.sqrt(np.mean((g_temps - c_temps) ** 2))
    logger.info(
        "Closed-loop temps RMSE between Graph and Classic hybrids: %.6f", temp_rmse
    )

    # plot with fixed y-axis and final error annotations
    plt.figure(figsize=(10, 6))
    plt.plot(g_temps, label="Graph Temp")
    plt.plot(c_temps, label="Classic Temp")
    plt.axhline(22.0, color="k", linestyle="--", label="Setpoint")
    # Set vertical axis scale to 0-28 as requested
    plt.ylim(0, 28)
    # annotate final absolute error values on the plot (upper-left)
    ax = plt.gca()
    info_text = f"Graph final_abs_error={gm:.3f}\nClassic final_abs_error={cm:.3f}"
    ax.text(
        0.02,
        0.95,
        info_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )
    plt.legend()
    plt.title("Closed-loop temperature (Graph vs Classic)")
    plt.xlabel("Time step")
    plt.ylabel("Temperature")
    plt.show()


def run_compare_once(master_seed=None, verbose=False):
    """Run one instance of the compare experiment. Returns a dict with results."""
    # generate data
    if master_seed is None:
        master_seed = np.random.randint(0, 2**31 - 1)
    if verbose:
        logger.debug("Experiment master_seed=%s", master_seed)
    X, y = generate_dataset_samples(1200, seed=master_seed)
    # split train/test
    n = len(X[0])
    idx = np.arange(n)
    # NOTE: preserve ordering (no shuffle) for deterministic, repeatable experiments
    # If random splits are desired, replace with a seeded shuffle here.
    train_idx = idx[: int(0.8 * n)]
    test_idx = idx[int(0.8 * n) :]

    X_train = [np.array(X[0])[train_idx].tolist(), np.array(X[1])[train_idx].tolist()]
    y_train = [np.array(y[0])[train_idx].tolist()]

    X_test = [np.array(X[0])[test_idx].tolist(), np.array(X[1])[test_idx].tolist()]
    y_test = [np.array(y[0])[test_idx].tolist()]

    import random

    # Ensure deterministic initial weights by seeding Python's RNG and numpy
    random.seed(master_seed)
    np.random.seed(master_seed)

    # Build an untrained graph MLP to capture initial weights
    mlp_graph, scalers = build_graph_mlp(X_train, y_train)

    # Initialize Classic MLP with the graph's starting weights so both start identically
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
    # Legacy delay synchronization removed: ClassicMLP now updates weights/biases immediately (no delay API).

    # Train both
    mlp_graph, full_graph, scalers = train_graph_mlp(
        X_train, y_train, epochs=80, itersPerEpoch=4, mlp=mlp_graph
    )

    # Classic training on same normalized data
    Xn_raw = np.vstack([np.array(X_train[0]), np.array(X_train[1])]).T
    Xn = np.column_stack(
        [
            (Xn_raw[:, 0] - scalers["x0_mean"]) / scalers["x0_std"],
            (Xn_raw[:, 1] - scalers["x1_mean"]) / scalers["x1_std"],
        ]
    )
    yn = (np.array(y_train[0]) - scalers["y_mean"]) / scalers["y_std"]
    yn = yn.reshape(-1, 1)
    # Train for 320 epochs with full batch (960 samples) to match Graph's 320 iterations
    classic.train(Xn, yn, epochs=320, batch_size=len(Xn), verbose=False)

    # run detached closed-loop evaluation for one representative episode (MLP->FIS detached)
    # Use a shared, random seed for fair comparison between Graph and Classic sims
    shared_seed = np.random.randint(0, 2**31 - 1)
    g_temps, g_powers, g_errors = closed_loop_simulation_graph_detached(
        mlp_graph,
        scalers,
        steps=200,
        target=22.0,
        rng_seed=shared_seed,
        verbose=verbose,
    )
    c_temps, c_powers, c_errors = closed_loop_simulation_classic_detached(
        classic, scalers, steps=200, target=22.0, rng_seed=shared_seed, verbose=verbose
    )

    # compute metrics
    def metrics(errors, powers):
        final_abs_error = np.abs(errors[-10:]).mean()
        energy = np.sum(np.array(powers) / 100.0)
        overshoot = np.max(-np.minimum(errors, 0.0))
        return dict(final_abs_error=final_abs_error, energy=energy, overshoot=overshoot)

    gm = metrics(g_errors, g_powers)
    cm = metrics(c_errors, c_powers)

    results = dict(
        master_seed=master_seed,
        shared_seed=shared_seed,
        g_temps=g_temps,
        g_powers=g_powers,
        g_errors=g_errors,
        c_temps=c_temps,
        c_powers=c_powers,
        c_errors=c_errors,
        graph_metrics=gm,
        classic_metrics=cm,
        scalers=scalers,
    )
    return results


def run_compare_multiple(n_runs=10, verbose=False, save_file=None, csv_file=None):
    """Run the experiment n_runs times and plot all temperature traces on a single graph.

    If `csv_file` is provided (or `save_file` with a .png extension is passed),
    export a per-trial CSV and Markdown table containing the master/shared seeds and
    the difference between final room temperature and the user preferred temperature
    (setpoint=22.0) for both Graph and Classic models.
    """
    seeds = np.random.randint(0, 2**31 - 1, size=n_runs)
    all_results = []
    for i, s in enumerate(seeds):
        if verbose:
            logger.debug("Running trial %s/%s seed=%s", i + 1, n_runs, s)
        res = run_compare_once(master_seed=int(s), verbose=verbose)
        all_results.append(res)

    # Plot all runs on one figure
    plt.figure(figsize=(12, 7))
    for res in all_results:
        plt.plot(res["g_temps"], color="tab:blue", alpha=0.25, linewidth=1)
        plt.plot(res["c_temps"], color="tab:orange", alpha=0.25, linewidth=1)

    # plot mean trajectories
    g_mean = np.mean([r["g_temps"] for r in all_results], axis=0)
    c_mean = np.mean([r["c_temps"] for r in all_results], axis=0)
    plt.plot(g_mean, color="tab:blue", linewidth=2, label="Graph mean")
    plt.plot(c_mean, color="tab:orange", linewidth=2, label="Classic mean")

    plt.axhline(22.0, color="k", linestyle="--", label="Setpoint")
    plt.ylim(0, 28)
    plt.legend()
    plt.title(f"Closed-loop temperature (Graph vs Classic) - {n_runs} runs")
    plt.xlabel("Time step")
    plt.ylabel("Temperature")

    # annotate mean final_abs_error
    gm_mean = np.mean([r["graph_metrics"]["final_abs_error"] for r in all_results])
    cm_mean = np.mean([r["classic_metrics"]["final_abs_error"] for r in all_results])
    info_text = f"Graph mean final_abs_error={gm_mean:.3f}\nClassic mean final_abs_error={cm_mean:.3f}"
    ax = plt.gca()
    ax.text(
        0.02,
        0.95,
        info_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )

    if save_file:
        plt.savefig(save_file, bbox_inches="tight")
        if verbose:
            logger.info("Saved consolidated plot to %s", save_file)

    # Export per-trial table of final temp differences and seeds (CSV + Markdown)
    if csv_file is None and save_file:
        # derive csv filename from provided plot filename by convention
        if isinstance(save_file, str) and save_file.lower().endswith(".png"):
            csv_file = save_file[:-4] + "_table.csv"
    if csv_file:
        rows = []
        target = 22.0
        for idx, r in enumerate(all_results, start=1):
            g_final = float(r["g_temps"][-1])
            c_final = float(r["c_temps"][-1])
            g_abs = abs(g_final - target)
            c_abs = abs(c_final - target)
            rows.append(
                {
                    "trial": idx,
                    "master_seed": int(r.get("master_seed", 0)),
                    "shared_seed": int(r.get("shared_seed", 0)),
                    "graph_final_temp": g_final,
                    "graph_abs_error": g_abs,
                    "classic_final_temp": c_final,
                    "classic_abs_error": c_abs,
                }
            )

        # compute summary rows: AVERAGE, DIFFERENCE (Graph - Classic), PERCENT_DIFF (relative to Classic)
        avg_graph_final = np.mean([r["graph_final_temp"] for r in rows])
        avg_classic_final = np.mean([r["classic_final_temp"] for r in rows])
        avg_graph_abs = np.mean([r["graph_abs_error"] for r in rows])
        avg_classic_abs = np.mean([r["classic_abs_error"] for r in rows])

        rows.append(
            {
                "trial": "AVERAGE",
                "master_seed": "",
                "shared_seed": "",
                "graph_final_temp": avg_graph_final,
                "graph_abs_error": avg_graph_abs,
                "classic_final_temp": avg_classic_final,
                "classic_abs_error": avg_classic_abs,
            }
        )

        diff_final = avg_graph_final - avg_classic_final
        diff_abs = avg_graph_abs - avg_classic_abs
        rows.append(
            {
                "trial": "DIFFERENCE",
                "master_seed": "",
                "shared_seed": "",
                "graph_final_temp": diff_final,
                "graph_abs_error": diff_abs,
                "classic_final_temp": "",
                "classic_abs_error": "",
            }
        )

        if avg_classic_final != 0:
            pct_final = (diff_final / avg_classic_final) * 100.0
        else:
            pct_final = float("inf")
        if avg_classic_abs != 0:
            pct_abs = (diff_abs / avg_classic_abs) * 100.0
        else:
            pct_abs = float("inf")

        rows.append(
            {
                "trial": "PERCENT_DIFF",
                "master_seed": "",
                "shared_seed": "",
                "graph_final_temp": pct_final,
                "graph_abs_error": pct_abs,
                "classic_final_temp": "",
                "classic_abs_error": "",
            }
        )

        fieldnames = [
            "trial",
            "master_seed",
            "shared_seed",
            "graph_final_temp",
            "graph_abs_error",
            "classic_final_temp",
            "classic_abs_error",
        ]
        try:
            with open(csv_file, "w", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            if verbose:
                logger.info("Exported per-trial table to %s", csv_file)
            md_file = csv_file.replace(".csv", ".md")
            with open(md_file, "w", encoding="utf-8") as fh:
                fh.write("| " + " | ".join(fieldnames) + " |\n")
                fh.write("|" + "|".join(["---"] * len(fieldnames)) + "|\n")
                for r in rows:
                    fh.write("| " + " | ".join(str(r[f]) for f in fieldnames) + " |\n")
            if verbose:
                logger.info("Exported per-trial markdown table to %s", md_file)
        except Exception:
            logger.exception("Failed to export per-trial table to %s", csv_file)

    plt.show()
    return all_results


if __name__ == "__main__":
    # Run the original single experiment for backward compatibility
    # and additionally run the experiment 10 times and show consolidated results.
    run_compare()
    # Now run the repeated experiment and display consolidated figure
    run_compare_multiple(n_runs=10, verbose=True, save_file="compare_10_runs.png")
