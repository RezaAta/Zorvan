"""Measure reference processor cost as node count grows.

This isolates `GraphProcessor` from `Graph.AddNode`, whose dense adjacency
matrix makes large graph construction quadratic in memory. The node list and
predecessor links are built directly for this runtime-only measurement.
"""

import argparse
import json
import time
from types import SimpleNamespace

import numpy as np

from zorvan_reference.Core.GraphProcessor import GraphProcessor
from zorvan_reference.Nodes.AdditionNode import AdditionNode
from zorvan_reference.Nodes.ContainerNode import ContainerNode
from zorvan_reference.Nodes.LinearNode import LinearNode
from zorvan_reference.Nodes.MultiplicationNode import MultiplicationNode
from zorvan_reference.Nodes.SigmoidNode import SigmoidNode


def benchmark_size(node_count, ticks):
    nodes = [
        LinearNode(f"n{index}", 1.0 if index == 0 else 0.0)
        for index in range(node_count)
    ]
    for index in range(1, node_count):
        nodes[index].AddPreNode(nodes[index - 1])
    for index, node in enumerate(nodes):
        node.id = str(index)
    graph = SimpleNamespace(nodes=nodes)
    processor = GraphProcessor(graph, max_workers=1, verbose=False)

    start = time.perf_counter()
    processor.ComputeGraph(iterations=ticks)
    reference_seconds = time.perf_counter() - start

    values = np.zeros(node_count, dtype=float)
    values[0] = 1.0
    start = time.perf_counter()
    for _ in range(ticks):
        values[1:] = values[:-1].copy()
    numpy_seconds = time.perf_counter() - start

    return {
        "nodes": node_count,
        "ticks": ticks,
        "reference_seconds": reference_seconds,
        "numpy_seconds": numpy_seconds,
        "reference_over_numpy": reference_seconds / numpy_seconds,
    }


def benchmark_width(width, rng):
    x = np.asarray([0.25, 0.75])
    w1 = rng.normal(size=(2, width))
    w2 = rng.normal(size=width)
    nodes = []

    def add(node):
        node.id = str(len(nodes))
        nodes.append(node)
        return node

    inputs = [add(ContainerNode(f"x{index}", value)) for index, value in enumerate(x)]
    hidden = []
    for index in range(width):
        products = []
        for input_index in range(2):
            weight = add(
                ContainerNode(f"w{input_index}_{index}", w1[input_index, index])
            )
            product = add(MultiplicationNode(f"mul{input_index}_{index}"))
            product.AddPreNode(inputs[input_index], weight)
            products.append(product)
        total = add(AdditionNode(f"sum{index}"))
        total.AddPreNode(*products)
        activation = add(SigmoidNode(f"h{index}"))
        activation.AddPreNode(total)
        hidden.append(activation)

    output_products = []
    for index, node in enumerate(hidden):
        weight = add(ContainerNode(f"wo{index}", w2[index]))
        product = add(MultiplicationNode(f"mout{index}"))
        product.AddPreNode(node, weight)
        output_products.append(product)
    output_sum = add(AdditionNode("output_sum"))
    output_sum.AddPreNode(*output_products)
    output = add(LinearNode("output"))
    output.AddPreNode(output_sum)

    ticks = max(4, width // 2 + 3)
    processor = GraphProcessor(
        SimpleNamespace(nodes=nodes), max_workers=1, verbose=False
    )
    start = time.perf_counter()
    processor.ComputeGraph(iterations=ticks)
    reference_seconds = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(ticks):
        hidden_values = 1.0 / (1.0 + np.exp(-(x @ w1)))
        _ = hidden_values @ w2
    numpy_seconds = time.perf_counter() - start
    return {
        "hidden_width": width,
        "nodes": len(nodes),
        "ticks": ticks,
        "reference_seconds": reference_seconds,
        "numpy_seconds": numpy_seconds,
        "reference_over_numpy": reference_seconds / numpy_seconds,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=[100, 1000, 10000, 100000]
    )
    parser.add_argument("--ticks", type=int, default=3)
    parser.add_argument(
        "--widths", nargs="+", type=int, default=[2, 4, 8, 16, 32, 64, 128, 256]
    )
    parser.add_argument("--output")
    args = parser.parse_args()
    result = {
        "benchmark": "identity chain runtime only",
        "graph_construction": "excluded; dense Graph adjacency is quadratic",
        "results": [benchmark_size(size, args.ticks) for size in args.sizes],
        "width_scaling": [
            benchmark_width(width, np.random.default_rng(42)) for width in args.widths
        ],
    }
    encoded = json.dumps(result, indent=2)
    print(encoded)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(encoded + "\n")


if __name__ == "__main__":
    main()
