"""Complex nodes (compressed/abstract) must not change concurrent-processing results.

Compression and abstraction are views over the flat graph: for every tick, the
externally observed values must match the uncompressed graph exactly
(trace equivalence). In particular, complex nodes must read their internal
inputs from the tick snapshot (Phase 1), never from live values in Phase 2.
"""

import pytest

from zorvan_reference.Core.Graph import Graph
from zorvan_reference.Core.GraphProcessor import GraphProcessor
from zorvan_reference.Nodes.AdditionNode import AdditionNode
from zorvan_reference.Nodes.DataStreamNode import DataStreamNode
from zorvan_reference.Nodes.MultiplicationNode import MultiplicationNode

DATA = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
TICKS = 8


def _trace(graph, observed, ticks=TICKS, single_thread=True):
    proc = GraphProcessor(graph, max_workers=1 if single_thread else 4, verbose=False)
    out = []
    for _ in range(ticks):
        if single_thread:
            proc.ComputeGraphSingleThread(1)
        else:
            proc.ComputeGraph(1)
        out.append(observed.value)
    return out


def _chain_graph():
    """src -> n1 -> n2 -> n3 -> out (Addition nodes pass a single input through)."""
    g = Graph()
    src = DataStreamNode("src", list(DATA))
    n1, n2, n3, out = (AdditionNode(n) for n in ("n1", "n2", "n3", "out"))
    g.AddNode(src, n1, n2, n3, out)
    g.ConnectPreNode(n1, src)
    g.ConnectPreNode(n2, n1)
    g.ConnectPreNode(n3, n2)
    g.ConnectPreNode(out, n3)
    return g, src, (n1, n2, n3), out


def _fan_graph():
    """src -> {a, b} -> out, where out = a + b."""
    g = Graph()
    src = DataStreamNode("src", list(DATA))
    a = AdditionNode("a")
    b = AdditionNode("b")
    out = AdditionNode("out")
    g.AddNode(src, a, b, out)
    g.ConnectPreNode(a, src)
    g.ConnectPreNode(b, src)
    g.ConnectPreNode(out, a, b)
    return g, src, (a, b), out


@pytest.mark.parametrize("single_thread", [True, False])
def test_compressed_chain_preserves_per_tick_trace(single_thread):
    flat, _, _, flat_out = _chain_graph()
    expected = _trace(flat, flat_out, single_thread=single_thread)

    g, _, chain, out = _chain_graph()
    assert g.CompressNodes(list(chain)) is not None
    actual = _trace(g, out, single_thread=single_thread)

    assert actual == expected


@pytest.mark.parametrize("single_thread", [True, False])
def test_abstract_group_preserves_per_tick_trace(single_thread):
    flat, _, _, flat_out = _fan_graph()
    expected = _trace(flat, flat_out, single_thread=single_thread)

    g, _, group, out = _fan_graph()
    assert g.AbstractNodes(list(group)) is not None
    actual = _trace(g, out, single_thread=single_thread)

    assert actual == expected


def test_compressed_chain_result_independent_of_node_order():
    """Processing order inside a tick must not matter (snapshot semantics)."""
    g1, _, chain1, out1 = _chain_graph()
    g1.CompressNodes(list(chain1))

    g2, _, chain2, out2 = _chain_graph()
    g2.CompressNodes(list(chain2))
    g2.nodes.reverse()

    assert _trace(g1, out1) == _trace(g2, out2)


def test_nested_compression_inside_abstraction_preserves_trace():
    """src -> {a1 -> a2, b1 -> b2} -> out, with each branch compressed, then abstracted."""

    def build():
        g = Graph()
        src = DataStreamNode("src", list(DATA))
        a1, a2 = AdditionNode("a1"), MultiplicationNode("a2")
        b1, b2 = AdditionNode("b1"), AdditionNode("b2")
        out = AdditionNode("out")
        g.AddNode(src, a1, a2, b1, b2, out)
        g.ConnectPreNode(a1, src)
        g.ConnectPreNode(a2, a1)
        g.ConnectPreNode(b1, src)
        g.ConnectPreNode(b2, b1)
        g.ConnectPreNode(out, a2, b2)
        return g, (a1, a2), (b1, b2), out

    flat, _, _, flat_out = build()
    expected = _trace(flat, flat_out)

    g, branch_a, branch_b, out = build()
    ca = g.CompressNodes(list(branch_a))
    cb = g.CompressNodes(list(branch_b))
    assert ca is not None and cb is not None
    assert g.AbstractNodes([ca, cb]) is not None

    assert _trace(g, out) == expected
