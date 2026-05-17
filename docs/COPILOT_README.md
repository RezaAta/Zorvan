# COPILOT_README

Purpose: A short, practical guide for AI coding assistants working on this repository.

Quick run commands (PowerShell):

```powershell
# Run the GUI
python run_new_ui.py

# Run a small XOR test
python Examples/exp_xor_classic_mlp.py

# Compare three approaches (benchmark)
python Experiments/exp_compare_three_approaches.py
```

Important files to inspect when debugging or changing behavior:
- `zorvan/Core/Graph.py` – core Graph class and node orchestration
- `zorvan/Core/GraphProcessor.py` – execution engine (concurrent & forward processing)
- `zorvan/Core/MLPGraph.py` – MLP implementation (concurrent, buffers)
- `zorvan/Core/MLPGraphForwardProcessing.py` – MLP (forward processing)
- `zorvan/Core/BackpropGraph.py` and `BackpropGraphForwardProcessing.py` – backprop implementations
- `zorvan/Nodes/ContainerNode.py` – trainable parameter container
- `zorvan/Nodes/BufferNode.py` – timing buffers used by concurrent mode
- `.github/copilot-instructions.md` – longer agent instructions and research context

Coding and edit guidelines for assistants:
- Make minimal, targeted edits. Prefer fixing root causes but avoid sweeping refactors.
- Preserve the node-centric design: nodes are active computational actors; keep their responsibilities local.
- Do not change buffer size formulas or synchronization timing without running tests and understanding the effect.
- When touching forward-processing code, ensure source nodes and `ContainerNode`s are marked processed for the first pass (see `PrepareForForwardProcessing`).
- Use existing naming conventions for weights (e.g., `W_x0H0N1`) when accessing/setting node values programmatically.
- Run small tests after edits: `Examples/exp_xor_classic_mlp.py` and `Experiments/exp_compare_three_approaches.py` are quick sanity checks.
- Naming convention: prefix experiment/demo scripts with `exp_` (e.g., `exp_xor_example.py`) so they are easy to find and not picked up by `pytest`.

What to do before making larger changes:
- Propose design changes in an issue or PR description and get confirmation before implementing core execution-model edits.
- Add or update tests that exercise the changed behavior.

If you need more context, read `.github/copilot-instructions.md` for the research thesis and detailed architecture notes.

New project policy and tooling:
- `CONTRIBUTING.md` – project contribution rules (TDD, commit style, testing guidance).
- `AGENT_POLICY.md` – high-level rules for AI-assisted edits and agent behavior.
- `DEVELOPER_GUIDE.md` – quick developer workflow including local commands, testing, and pre-commit guidance.
Install `commitizen` and use `git cz` to create Conventional Commits; `pre-commit` is supported for local checks.
