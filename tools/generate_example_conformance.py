"""Generate fixed-seed traces for registered and end-to-end examples."""

import json
import random
import re
import tempfile
from pathlib import Path

import numpy as np

from zorvan_reference.Core.CGJsonIO import save
from zorvan_reference.Examples.ANFIS_XOR_Concurrent import build_anfis_xor
from gui_framework.legacy.examples_loader import ExamplesLoader

try:
    from .record_conformance import record_case
except ImportError:
    from record_conformance import record_case


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _write_case(graph, inputs, output_dir):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        graph_file = temp_dir / "graph.cgjson"
        inputs_file = temp_dir / "inputs.json"
        save(graph, str(graph_file))
        inputs_file.write_text(json.dumps(inputs), encoding="utf-8")
        record_case(graph_file, inputs_file, output_dir)


def generate(output_root="conformance"):
    random.seed(1729)
    np.random.seed(1729)
    output_root = Path(output_root)
    loader = ExamplesLoader()
    for category in loader.get_categories():
        for name, _description, builder in category.examples:
            random.seed(1729)
            np.random.seed(1729)
            graph = builder()
            mode = (
                "forward"
                if category.name.endswith("forward")
                else "manual" if category.name.endswith("manual") else "concurrent"
            )
            ticks = 24 if "Fibonacci" in name else 20 if "XOR" in name else 5
            inputs = {
                "ticks": ticks,
                "processor": mode,
                "max_workers": 1,
                "random_seed": 1729,
            }
            _write_case(
                graph,
                inputs,
                output_root / "examples" / _slug(category.name) / _slug(name),
            )

    random.seed(1729)
    np.random.seed(1729)
    graph, _processor, x1, x2, _output, _params = build_anfis_xor()
    xor_samples = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]
    events = []
    for index, (a, b) in enumerate(xor_samples):
        tick = 1 + index * 6
        events.extend(
            [
                {"tick": tick, "node_id": x1.id, "value": a},
                {"tick": tick, "node_id": x2.id, "value": b},
            ]
        )
    _write_case(
        graph,
        {
            "ticks": 24,
            "processor": "concurrent",
            "max_workers": 1,
            "random_seed": 1729,
            "events": events,
        },
        output_root / "end_to_end" / "anfis_xor",
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="conformance")
    generate(parser.parse_args().output)
