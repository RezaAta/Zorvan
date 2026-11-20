"""Record per-tick traces from the Python reference engine."""

import argparse
import json
import random
import zipfile
from pathlib import Path

from zorvan_reference.Core.CGJsonIO import _serialize_value, load
from zorvan_reference.Core.GraphProcessor import GraphProcessor


def _seed_random_generators(inputs):
    if "random_seed" not in inputs:
        return
    random.seed(inputs["random_seed"])
    try:
        import numpy as np

        np.random.seed(inputs["random_seed"])
    except ImportError:
        pass


def _advance_tick(processor, mode, forward_sequence, tick):
    if mode == "concurrent":
        processor.ComputeGraph(1)
    elif mode == "manual":
        processor.ManualProcessing(1)
    elif forward_sequence:
        step_nodes = forward_sequence[(tick - 1) % len(forward_sequence)]
        for node in step_nodes:
            if not getattr(node, "midCalculation", False):
                node.UpdateInputs()
        for node in step_nodes:
            node.ProcessBatch()
        processor.time += 1


def _snapshot_values(graph):
    return {str(node.id): _serialize_value(node.value) for node in graph.nodes}


def record_trace(graph, inputs):
    """Run a graph and return its node values after each requested tick.

    `inputs` accepts `ticks`, optional `max_workers`, `initial_values` keyed by
    node ID, and optional `events` containing `tick`, `node_id`, and `value`.
    An event is applied immediately before its one-based tick.
    """
    _seed_random_generators(inputs)
    nodes_by_id = {str(node.id): node for node in graph.nodes}
    for node_id, value in inputs.get("initial_values", {}).items():
        nodes_by_id[str(node_id)].value = value

    events_by_tick = {}
    for event in inputs.get("events", []):
        events_by_tick.setdefault(int(event["tick"]), []).append(event)

    mode = inputs.get("processor", "concurrent")
    processor = GraphProcessor(
        graph,
        max_workers=inputs.get("max_workers", 1),
        verbose=False,
    )
    forward_sequence = None
    if mode == "forward":
        forward_sequence = processor.find_execution_sequence().get("sequence", [])
    elif mode not in {"concurrent", "manual"}:
        raise ValueError(f"Unsupported processor mode: {mode}")

    ticks = []
    for tick in range(1, int(inputs["ticks"]) + 1):
        for event in events_by_tick.get(tick, []):
            nodes_by_id[str(event["node_id"])].value = event["value"]
        _advance_tick(processor, mode, forward_sequence, tick)
        ticks.append({"tick": tick, "values": _snapshot_values(graph)})

    return {
        "trace_version": 1,
        "processor": mode,
        "tolerance": {"absolute": 1e-9, "relative": 1e-7},
        "ticks": ticks,
    }


def _read_graph_document(path):
    if path.suffix.lower() in {".cgz", ".zip"}:
        with zipfile.ZipFile(path) as archive:
            return json.loads(archive.read("graph.json"))
    return json.loads(path.read_text(encoding="utf-8"))


def record_case(graph_path, inputs_path, output_dir):
    graph_path = Path(graph_path)
    inputs_path = Path(inputs_path)
    output_dir = Path(output_dir)
    graph_document = _read_graph_document(graph_path)
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    graph = load(str(graph_path))
    trace = record_trace(graph, inputs)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "graph.json").write_text(
        json.dumps(graph_document, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "inputs.json").write_text(
        json.dumps(inputs, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "trace.json").write_text(
        json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", help="input .cgjson, .json, or .cgz graph")
    parser.add_argument("inputs", help="JSON tick and input-event specification")
    parser.add_argument("output", help="output conformance case directory")
    args = parser.parse_args()
    record_case(args.graph, args.inputs, args.output)


if __name__ == "__main__":
    main()
