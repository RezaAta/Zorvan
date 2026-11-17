# Copilot Instructions

The full agent guide is **`AGENTS.md`** at the repository root: commands,
repository map, execution semantics, conventions. Read it before making changes.
The essentials:

- **Ask before any git write**: no branches, commits, pushes, tags, merges or
  rebases without the maintainer's explicit approval for that specific action.
- **Test first**; every behavioural change needs a test and a doc update.
  Fast check: `python -m pytest -q Tests/core`.
- **Preserve concurrent-processing semantics**: snapshot inputs in Phase 1,
  compute in Phase 2; results must not depend on node order; inputs are ordered
  by connection order; compressed/abstract nodes must not change per-tick
  results.
- **Nodes are the actors**: keep node logic inside nodes
  (`zorvan/Nodes/`); graphs orchestrate (`zorvan/Core/`).
- Execution-model changes need approval and a decision-log entry in
  `docs/REARCHITECTURE_PLAN.md`.
