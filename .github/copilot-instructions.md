# Copilot Instructions

The full agent guide is **`AGENTS.md`** at the repository root: commands,
repository map, execution semantics, conventions. Read it before making changes.
The essentials:

- **Ask before any git write**: no branches, commits, pushes, tags, merges or
  rebases without the maintainer's explicit approval. Propose the whole batch
  (commits, branch, push) at once; one approval covers that proposal.
- **Test first**; every behavioural change needs a test and a doc update.
  Fast check: `python -m pytest -q reference/Tests/core`.
- **Preserve concurrent-processing semantics**: snapshot inputs in Phase 1,
  compute in Phase 2; results must not depend on node order; inputs are ordered
  by connection order; compressed/abstract nodes must not change per-tick
  results.
- **Nodes are the actors**: keep node logic inside nodes
  (`reference/zorvan_reference/Nodes/`); graphs orchestrate (`reference/zorvan_reference/Core/`).
- Execution-model changes need approval and a decision-log entry in
  `docs/REARCHITECTURE_PLAN.md`.
