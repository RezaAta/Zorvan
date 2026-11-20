# Reference conformance cases

Each case contains `graph.json` (CGJSON graph document), `inputs.json` (tick
count, processor mode, optional seed and input events), and `trace.json`
(per-tick values for every top-level graph node). Trace metadata declares
absolute tolerance `1e-9` and relative tolerance `1e-7` for numeric values;
other serialized values compare exactly.

Cases were generated from the current Python reference on 2026-11-20:

- `nodes/`: one case for each of the 43 concrete built-in graph node kinds.
- `examples/`: all 13 graphs registered by the existing GUI examples loader,
  including Fibonacci, concurrent and forward MLPs, manual XOR, ANFIS, and EA.
- `end_to_end/anfis_xor/`: the standalone ANFIS XOR builder with four input
  events and a fixed seed.

Regenerate with:

```powershell
python tools/generate_node_conformance.py
python tools/generate_example_conformance.py
```

The recorder reloads each CGJSON graph before execution. The current corpus
does not yet translate every individual `reference/Tests/core` test scenario into a
portable case, and external custom node kinds are outside the built-in catalog.
