# AGENTS.md

Guide for AI coding agents (Claude Code, Copilot, Codex, ...) working in this
repository. Human contributors: see `CONTRIBUTING.md` and
`docs/DEVELOPER_GUIDE.md`; the rules below apply to you too.

## Ground rules (read first)

1. **Ask before any git write.** Don't create branches (or worktrees used as
   branches), commit, push, tag, merge, rebase or rewrite history without the
   maintainer's explicit approval **for that specific action**. Approval for one
   commit doesn't cover the next. When work is ready, propose the commit(s): the
   message and the files. Read-only git (`status`, `diff`, `log`, `show`) is fine.
2. **Test first.** Write a failing test, make it pass, then refactor. Every
   behavioural change needs a test; every user-visible change needs a doc update
   (and an entry under "Unreleased" in `CHANGELOG.md`).
3. **Small, focused changes.** One logical change per commit, with Conventional
   Commit messages (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
4. **Execution-model changes need approval.** Anything that changes processing
   semantics or timing must be agreed first and recorded in the decision log of
   `docs/REARCHITECTURE_PLAN.md`.
5. **Report honestly.** Say what you ran and what you didn't. If tests fail or
   were skipped, say so and include the output.

## Project in one paragraph

Zorvan builds AI models (MLPs, fuzzy systems, evolutionary algorithms, hybrids)
from micro-operation **nodes** wired into graphs. The graph is also the UI (a
PyQt6 editor). Graphs orchestrate, and **nodes are the actors**: keep node logic
inside nodes. The direction (Rust engine, TypeScript/Tauri UI, Python SDK, with
the current Python code as the behavioural reference) is in
`docs/REARCHITECTURE_PLAN.md`; read it before large refactors.

## Commands (Windows PowerShell; bash equivalents work in Git Bash)

```powershell
.\scripts\bootstrap.ps1 -InstallGui        # install deps (+ GUI deps)
python -m pytest -q Tests/core              # core suite: fast, run on every change
$env:QT_QPA_PLATFORM="offscreen"; python -m pytest -q Tests/gui_tests/unit/<area>   # GUI tests by area
python -m ruff check zorvan gui_framework Tests   # lint (advisory in CI)
python -m black --check . ; python -m isort --check-only .   # formatting
.\scripts\run_checks.ps1                    # core tests; -All for full suite, -Precommit for hooks
python run_new_ui.py                        # launch the editor
python zorvan/Examples/FibonacciExample.py  # quick sanity script
```

Use `python -m <tool>`: the tool executables may not be on PATH.

**Known test-environment issues (Windows):**
- Some custom-node GUI tests open modal dialogs (`exec()`) and hang when there
  is no display.
- The full GUI suite can crash natively inside Qt (access violation); this
  happens on a clean checkout too.

Run `Tests/core` plus the GUI test directories related to your change, not the
whole GUI suite. CI runs `Tests/core` on Python 3.10/3.11 plus a GUI smoke test.

## Repository map

- `zorvan/Core/`: `Graph.py` (structure, topology types, compression and
  abstraction, simplification, cycles), `GraphProcessor.py` (concurrent, forward
  and manual processing), MLP/backprop/ANFIS graph builders, `CGJsonIO.py`
  (`.cgjson`/`.cgz` persistence; Draw.io export is deprecated).
- `zorvan/Nodes/`: node types. Base classes: `Node`, `BasicNode`; complex nodes:
  `CompressedNode`, `AbstractNode`.
- `zorvan/Examples/`: runnable demo scripts (not tests).
- `gui_framework/`: PyQt6 editor. Entry point `run_new_ui.py` →
  `gui_framework/main_window.py`. MVVM layer: `viewmodels/`, `views/`,
  `adapters/`, `state/`, `events/`, `commands/`. Most widgets (canvas, node
  registry, examples loader, plots, controllers) live in
  `gui_framework/legacy/`.
- `Tests/core/` (engine) and `Tests/gui_tests/{unit,integration}/` (GUI, by
  feature area). Templates in `Tests/templates/`.
- `tools/`: one-off debug and repro scripts (run with the repo root on
  `PYTHONPATH`).
- `docs/`: guides; `docs/gui_rebuild/` is an archived record.

## Execution semantics (must be preserved)

- **Concurrent processing** (`GraphProcessor.ComputeGraph`) is the primary,
  validated mode. Each tick: (1) every node that isn't mid-calculation calls
  `UpdateInputs()` and snapshots its predecessors' values; (2) every node calls
  `ProcessBatch()` using only that snapshot. Results must not depend on node
  order. A path of k nodes takes k ticks; nodes don't wait for inputs.
- **Forward** and **manual** processing exist but are experimental.
- **Inputs are ordered** by connection order. Don't reorder `node.predecessors`;
  nodes like GaussianMembership, Subtraction and Division depend on position.
- **Node functions are deterministic procedures** `F(Input, t) → y`. Batching
  and mid-calculation state belong to the processor. Memory goes in the node's
  value plus a self-loop; prefer `t` over private counters; avoid global random
  state.
- **Complex nodes are views.** Compressing or abstracting must not change
  per-tick values (`Tests/core/graph/test_complex_node_snapshot_semantics.py`).
- **Simplification** never splits nodes on cycles (`simplify_fully` only
  splits on acyclic graphs).

## Conventions and gotchas

- Call `graph.UpdateAdjacencyMatrix()` after changing connections manually.
- Weight names: `W_x{input}H{layer}N{neuron}`, `W_H{layer}N{neuron}y{output}`.
- `MLPGraph.LoadData` takes **features × samples**;
  `MLPGraphForwardProcessing` takes **samples × features**.
- Concurrent MLP buffer sizes derive from `layersAhead`; don't change them
  casually. If training explodes, check gradient wiring and learning rate
  before suspecting buffers.
- Forward processing needs `mlp.PrepareForForwardProcessing(processor)` before
  training (the GUI does this automatically).
- Each node outputs one value (a value may be any data: number, list, ...).
- `GraphProcessor` stays single-threaded below 1000 nodes (the GIL dominates).
- New node type: class in `zorvan/Nodes/` (implement `Operation` and
  `IsValidInput`), a derivative node if differentiable, register it in
  `gui_framework/legacy/node_registry.py`, add tests in `Tests/core/nodes/`.
- Experiments and benchmarks are not tests: name them `exp_*.py`
  (`docs/EXPERIMENTS.md`).
- Line length 88; black + isort (profile black); ruff rules E, F, W, C.

## Vocabulary

- **Fusion hybrid**: changes a model's internals (e.g. ANFIS, mixed activations
  in one layer); in Zorvan, rewiring nodes.
- **Modular hybrid**: whole models cooperate (hierarchical or network).
- **Tick / step / iteration**: one round of concurrent processing.
