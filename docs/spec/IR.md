# Graph intermediate representation

Status: **Accepted proposal** · Target: Rust engine and portable graph files

The IR is a versioned, language-neutral description of model behavior. It is
separate from view state so the same model can be executed without a desktop
layout. This proposal does not change `.cgjson` or the Python serializer.

## Document shape

```json
{
  "format": "zorvan-ir",
  "version": 1,
  "model": {
    "nodes": [],
    "edges": [],
    "scheduler": { "kind": "concurrent" }
  },
  "view": {
    "nodes": {},
    "groups": []
  }
}
```

`model.nodes` is an array of node records. Each record has a stable `id`, a
`kind` identifier, an optional display `name`, a `parameters` object, and an
`initial_value`. Node-specific parameters are defined by the node catalog.
Unknown node kinds are load errors unless a registered plugin provides them.

`model.edges` is an ordered array. Each edge has a stable `id`, `source`,
`target`, and optional non-negative `delay` (default `0`). The order of edges
entering a target defines input order. Parallel edges are distinct. Self-loops
are valid. Delay semantics are not implemented in the Python reference and
must be specified before runtime support is claimed.

`view.nodes` maps node IDs to optional position, size, color, and collapsed
state. View data never changes execution. Groups reference member IDs and
represent visual simplification only.

## Values

Version 1 reserves tagged values for `f64`, `i64`, `bool`, `string`, and
recursive `list`. Additional value kinds require a versioned extension or a
new IR version. Non-finite floats need an explicit encoding because standard
JSON does not support them. This set is deliberately narrower than the open
Python value domain; custom nodes may define portable encodings.

## Versioning and compatibility

The top-level `version` is a positive integer. Readers must reject an
unsupported major schema version with a useful error. Additive optional fields
may be introduced compatibly; changing field meaning, ordering rules, value
encoding, or execution semantics requires a new version and migration. A
migration must preserve the original source file and report lossy conversions.
Node kind parameter schemas are versioned independently through an optional
`kind_version` field.

## `.cgjson` import mapping

The current serializer in `reference/zorvan_reference/Core/CGJsonIO.py` writes `metadata.format`
`CGJSON`, `metadata.version`, a top-level `nodes` array and `edges` array, plus
`graph`, `custom_nodes`, and optional canvas data. An importer should map:

- node `id`, `type`, `name`, and serializable `attrs` to IR identity, `kind`,
  name, and parameters/initial value;
- edge endpoints to IR `source` and `target`, preserving serialized edge order;
- canvas position and appearance fields to `view`, never to model parameters;
- embedded custom node definitions to a plugin/node-kind registry entry.

Compressed-node `internal_nodes` and abstract-node membership need explicit
flattening rules. They cannot be imported by guessing from display names. The
initial importer should preserve them as complex view records only when their
internal topology and values can be represented without changing traces;
otherwise it must fail with a conversion report rather than silently merge
them. Buffer-node conversion to delay edges remains an open product decision.

## Open design points

- Canonical schema for node parameters and custom node definitions.
- Whether view state lives in the same file or a sibling view document.
- Stable ID requirements when importing legacy files with missing IDs.
- Delay-edge initialization and its relationship to existing BufferNode
  patterns.
- Representation of values outside the built-in scalar/list set.
