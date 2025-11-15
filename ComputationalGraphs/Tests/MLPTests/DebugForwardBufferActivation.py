"""
Debug script to observe activation of error BufferNodes and MovingAverageNodes
in ForwardProcessing mode. Runs a small number of iterations with verbose output
and prints buffer contents.
"""
from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from ComputationalGraphs.Core.BackpropGraphForwardProcessing import BackpropGraphForwardProcessing
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
from ComputationalGraphs.Nodes.LinearNode import LinearNode
import time

# Small XOR dataset
X_train = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
y_train = [[0.0], [1.0], [1.0], [0.0]]

# Build small MLP forward
mlp = MLPGraphForwardProcessing(numInputs=2, numOutputs=1, numHiddenLayers=1, activationFunction=SigmoidNode, outputLayerType=LinearNode)
mlp.BuildMLP()
backprop = BackpropGraphForwardProcessing(mlp, learningRate=0.5)
backprop.BuildBackprop()

fullGraph = Graph()
for node in mlp.nodes:
    fullGraph.AddNode(node)
for node in backprop.nodes:
    fullGraph.AddNode(node)

fullGraph.starting_nodes = mlp.starting_nodes + [backprop.lrNode]

# Create processor with verbose True
processor = GraphProcessor(fullGraph, verbose=True)

# Load data and prepare
mlp.LoadData(X_train, y_train)

# Create small error buffers
total_iterations = mlp.GetPassLength() * len(X_train) * 5  # 5 epochs worth
error_buffers = mlp.CreateErrorBuffers(total_iterations, allowNone=True)
fullGraph.AddNode(*error_buffers)
fullGraph.UpdateAdjacencyMatrix()

# Reset processor forward state and prepare for forward processing AFTER adding buffers
processor.reset_forward_state()
prep_counts = mlp.PrepareForForwardProcessing(processor)
print(f"PrepareForForwardProcessing (post-buffer): sources={prep_counts[0]}, containers={prep_counts[1]}")

# Run forward processing with verbose to observe activations
print("\nRunning debug ForwardProcessing (verbose) for", total_iterations, "iterations\n")
start = time.time()
processor.ForwardProcessing(iterations=total_iterations)
end = time.time()
print(f"Debug run completed in {end-start:.2f}s")

# Print buffer contents summary
print("\nError buffer contents after debug run:")
for i, buf in enumerate(error_buffers):
    total = len(buf.buffer)
    non_none = len([v for v in buf.buffer if v is not None])
    print(f"  Buffer {i}: size={total}, non-None={non_none}")
    print("    sample first 20:", buf.buffer[:20])

print("\nDone")
