from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Core.MLPAnfisGraph import MLPAnfisGraph


def run_smoke():
    # Build ANFIS-style MLPGraph
    g = MLPAnfisGraph(numInputs=2, numOutputs=1, mfs_per_input=2)
    g.BuildMLP()

    # Display the graph for visual inspection
    try:
        g.DisplayGraph("ANFIS_MLPGraph_XOR")
    except Exception as ex:
        print("DisplayGraph failed:", ex)

    # Single-threaded processor for deterministic propagation
    gp = GraphProcessor(g, verbose=True)

    # Simple test inputs for XOR cases
    cases = [((0.0, 0.0), 0.0), ((0.0, 1.0), 1.0), ((1.0, 0.0), 1.0), ((1.0, 1.0), 0.0)]

    print("Running forward passes (no training)")
    for inp, tgt in cases:
        # Set DataStreamNode values directly
        g.inputLayer[0][0].value = inp[0]
        g.inputLayer[1][0].value = inp[1]
        # Run a few concurrent iterations to propagate
        gp.ComputeGraphSingleThread(6)
        # output node stored in outputLayer as (numerator, DivisionNode)
        out_node = g.outputLayer[0][1]
        print(f"in={inp} target={tgt} out={out_node.value}")


if __name__ == "__main__":
    run_smoke()
