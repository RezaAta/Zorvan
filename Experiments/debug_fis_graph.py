import os
import runpy

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.DivisionNode import DivisionNode
from ComputationalGraphs.Nodes.MaxNode import MaxNode
from ComputationalGraphs.Nodes.MinNode import MinNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
from ComputationalGraphs.Nodes.PiecewiseLinearNode import PiecewiseLinearNode

exp_ns = runpy.run_path(
    os.path.join(os.path.dirname(__file__), "HybridTempPredictionComparison.py")
)
fis_classic = exp_ns["fis_classic"]


def inspect(err, dp):
    full = Graph()
    err_in = DisplayNode("ErrIn", value=err)
    dp_in = DisplayNode("DpIn", value=dp)
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
    zero_c = DisplayNode("MinPower", 0.0)
    hundred_c = DisplayNode("MaxPower", 100.0)
    maxed = MaxNode("AtLeastZero")
    maxed.AddPreNode(out, zero_c)
    clamped = MinNode("ClampedPower")
    clamped.AddPreNode(maxed, hundred_c)
    full.AddNode(zero_c, hundred_c, maxed, clamped)
    full.starting_nodes = [err_in, dp_in]
    full.UpdateAdjacencyMatrix()
    proc = GraphProcessor(full, verbose=False)
    # Give the processor more iterations to ensure batch-style nodes converge
    proc.ComputeGraphSingleThread(50)
    print(f"err={err}, dp={dp}, class={fis_classic(err, dp)}, graph={clamped.value}")
    for n in full.nodes:
        print(n.name, type(n).__name__, getattr(n, "value", None))


if __name__ == "__main__":
    inspect(0.0, 0.0)
