from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode


def measure_delay(H, totalIterations=200):
    print(f"\nMeasuring backprop delay for H={H}")
    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=H,
        activationFunction=SigmoidNode,
        outputLayerType=LinearNode,
    )
    mlp.BuildMLP()
    bp = BackpropGraph(mlp, learningRate=0.1)
    bp.BuildBackprop()
    full = Graph()
    for n in mlp.nodes:
        full.AddNode(n)
    for n in bp.nodes:
        full.AddNode(n)
    full.UpdateAdjacencyMatrix()

    # single-sample dataset
    X = [[1.0], [0.0]]
    y = [[1.0]]
    mlp.LoadData(X, y)

    # Warmup forward pipeline
    proc_warm = GraphProcessor(mlp, verbose=False)
    networkLength = 3 * (len(mlp.hiddenLayers) + 1)
    proc_warm.ComputeGraph(networkLength)

    # prepare for training-like run with error buffers
    mlp.CreateErrorBuffers(bufferSize=totalIterations, mse_buffer_size=1)
    for eb in mlp.errorBuffers:
        if eb not in full.nodes:
            full.AddNode(eb)

    # collect nodes
    error_nodes = mlp.errorLayer
    weight_nodes = []
    for layer in mlp.weightLayers:
        for row in layer:
            for w in row:
                weight_nodes.append(w)

    # initialize histories
    weight_vals = {w.name: [] for w in weight_nodes}
    error_vals = {e.name: [] for e in error_nodes}

    proc = GraphProcessor(full, verbose=False)
    first_error_iter = None
    first_weight_change = {w.name: None for w in weight_nodes}

    # Run iterations
    for it in range(totalIterations):
        proc.ComputeGraph(1)
        # record error values
        for e in error_nodes:
            error_vals[e.name].append(e.value)
        # detect first error iteration (value not None)
        if first_error_iter is None:
            # If any error node has a non-None value, mark first_error_iter
            for e in error_nodes:
                if e.value is not None:
                    first_error_iter = it
                    break
        # record weight values and detect changes
        for w in weight_nodes:
            weight_vals[w.name].append(w.value)
            if first_weight_change[w.name] is None:
                # compare to previous value if exist; else compare to initial
                if len(weight_vals[w.name]) >= 2:
                    if weight_vals[w.name][-1] != weight_vals[w.name][-2]:
                        first_weight_change[w.name] = it
    # Report
    print(f"first_error_iter (after warmup) = {first_error_iter}")
    for layer_idx, layer in enumerate(mlp.weightLayers):
        print(f"Weight layer {layer_idx}:")
        for row_idx, row in enumerate(layer):
            for col_idx, w in enumerate(row):
                meas = first_weight_change[w.name]
                d = None
                if meas is not None and first_error_iter is not None:
                    d = meas - first_error_iter
                print(f"  {w.name}: first_update_iter={meas}, d = {d}")


if __name__ == "__main__":
    for H in [1, 2]:
        measure_delay(H, totalIterations=300)
