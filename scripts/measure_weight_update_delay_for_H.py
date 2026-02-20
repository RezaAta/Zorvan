import numpy as np

from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.SigmoidNode import SigmoidNode


def theoretical_delays(numHiddenLayers):
    H = numHiddenLayers
    forward_len = 3 * (H + 1)
    delays = {}
    # weight layers indexed 0..H where H is last (hidden->output)
    D_next = forward_len + 2
    delays[H] = D_next
    for l in range(H - 1, -1, -1):
        layersAhead = H - l
        weightNodeBuffer = (layersAhead * 6) - 1
        D_next = D_next + weightNodeBuffer
        delays[l] = D_next
    return forward_len, delays


def measure_for_H(H, totalIterations=200):
    print(f"Measuring for H={H}")
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

    # single sample
    X = [[1.0], [0.0]]
    y = [[1.0]]
    mlp.LoadData(X, y)

    mlp.CreateErrorBuffers(bufferSize=totalIterations, mse_buffer_size=1)
    for eb in mlp.errorBuffers:
        if eb not in full.nodes:
            full.AddNode(eb)

    weight_nodes = []
    for layer in mlp.weightLayers:
        for row in layer:
            for w in row:
                weight_nodes.append(w)

    proc = GraphProcessor(full, verbose=False)
    # Warmup network so buffers are filled as in normal training runs
    networkLength = 3 * (len(mlp.hiddenLayers) + 1)
    mwarm = GraphProcessor(mlp, verbose=False)
    mwarm.ComputeGraph(networkLength)

    history = {w.name: [] for w in weight_nodes}

    for it in range(totalIterations):
        proc.ComputeGraph(1)
        for w in weight_nodes:
            history[w.name].append(w.value)

    # analyze changes
    measured = {}
    for w in weight_nodes:
        hist = history[w.name]
        changes = [i for i in range(1, len(hist)) if hist[i] != hist[i - 1]]
        measured[w.name] = changes[0] if changes else None

    # compute theory
    forward_len, delays = theoretical_delays(H)

    print(f"forward_len={forward_len}")
    for idx, layer in enumerate(mlp.weightLayers):
        print(
            f"Weight layer index {idx} (source layer {'input' if idx==0 else 'hidden'+str(idx-1)})"
        )
        # layer is list of rows (source dimension x dest dimension)
        for i, row in enumerate(layer):
            for j, wnode in enumerate(row):
                name = wnode.name
                meas = measured.get(name)
                theory = delays[idx]
                print(f"  {name}: measured_update_iter={meas}, theory_delay={theory}")
    print("")


if __name__ == "__main__":
    for H in [1, 2]:
        measure_for_H(H, totalIterations=300)
