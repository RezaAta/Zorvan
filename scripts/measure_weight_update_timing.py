import numpy as np

from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.LinearNode import LinearNode

# Build a minimal MLPGraph with H=1
from zorvan.Nodes.SigmoidNode import SigmoidNode

mlp = MLPGraph(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,
)
mlp.BuildMLP()
# Initialize Backprop
bp = BackpropGraph(mlp, learningRate=0.1)
bp.BuildBackprop()
# Combine
from zorvan.Core.Graph import Graph

full = Graph()
for node in mlp.nodes:
    full.AddNode(node)
for node in bp.nodes:
    full.AddNode(node)
full.UpdateAdjacencyMatrix()

# Load a single-sample dataset: X = [x0,x1]; y = [y]
X = [[1.0], [0.0]]
y = [[1.0]]
mlp.LoadData(X, y)

# Prepare for training: create error buffers and such
totalIterations = 60
mlp.CreateErrorBuffers(bufferSize=totalIterations, mse_buffer_size=1)
for eb in mlp.errorBuffers:
    if eb not in full.nodes:
        full.AddNode(eb)
for mse in mlp.mseNodes:
    if mse not in full.nodes:
        full.AddNode(mse)

# Find weight nodes
weight_nodes = []
for layer in mlp.weightLayers:
    for row in layer:
        for w in row:
            weight_nodes.append(w)

# Record weight values over iterations
weights_history = {w.name: [] for w in weight_nodes}

proc = GraphProcessor(full, verbose=False)
# Run graph for many iterations and record weight values
for it in range(totalIterations):
    proc.ComputeGraph(1)  # advance one iteration
    for w in weight_nodes:
        weights_history[w.name].append(w.value)

# Print when weight values change
for name, hist in weights_history.items():
    changes = [i for i in range(1, len(hist)) if hist[i] != hist[i - 1]]
    print(name, "changed at iterations:", changes)
    print(name, "values:", hist[:30])
