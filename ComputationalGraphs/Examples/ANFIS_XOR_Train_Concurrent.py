"""Train MLPAnfisGraph on XOR using BackpropAnfisGraph (concurrent).

This example wires the ANFIS graph and its ANFIS-specific backprop graph
into a combined `Graph` and runs concurrent training similar to the
existing MLP examples.
"""
from ComputationalGraphs.Core.MLPAnfisGraph import MLPAnfisGraph
from ComputationalGraphs.Core.BackpropAnfisGraph import BackpropAnfisGraph
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor


def run_training(epochs=50, learning_rate=0.5):
    # Build ANFIS graph
    mlp = MLPAnfisGraph(numInputs=2, numOutputs=1, mfs_per_input=2)
    mlp.BuildMLP()

    # Attach backprop for ANFIS consequents
    back = BackpropAnfisGraph(mlp, learningRate=learning_rate)
    back.BuildBackprop()

    # Combine graphs into a single Graph for processing
    combined = Graph()
    for n in mlp.nodes:
        combined.AddNode(n)
    for n in back.nodes:
        combined.AddNode(n)

    processor = GraphProcessor(combined, verbose=False)

    # Display combined graph for inspection (try/catch in case Graphviz not available)
    try:
        combined.DisplayGraph("ANFIS_Combined_Train")
    except Exception:
        pass

    # XOR data (transposed form expected by MLP.LoadData)
    X = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]
    y = [[0.0, 1.0, 1.0, 0.0]]
    mlp.LoadData(X, y)

    total_iterations = epochs * 4

    # Create error buffers to capture MSE across iterations (optional)
    mlp.CreateErrorBuffers(total_iterations)
    for eb in mlp.errorBuffers:
        combined.AddNode(eb)

    # Warmup
    networkLength = 3 * (mlp.numHiddenLayers + 1)
    processor.ComputeGraph(networkLength)

    # Train
    print("Starting concurrent ANFIS training (consequents only)")
    processor.ComputeGraph(total_iterations)

    # Print final outputs for each XOR sample
    print("Final outputs:")
    for i in range(4):
        # set inputs to each sample and run a few steps to get output
        mlp.inputLayer[0][0].value = X[0][i]
        mlp.inputLayer[1][0].value = X[1][i]
        processor.ComputeGraphSingleThread(6)
        out = mlp.outputLayer[0][1]
        print(f"sample {i}: in=({X[0][i]},{X[1][i]}) out={out.value:.4f}")


if __name__ == '__main__':
    run_training(epochs=60, learning_rate=0.3)
