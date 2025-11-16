# COPILOT_README

Purpose: A short, practical guide for AI coding assistants working on this repository.

Quick run commands (PowerShell):

```powershell
# Run the GUI
python run_gui.py

# Run a small XOR test
python ClassicMLPTestOnXOR.py

# Compare three approaches (benchmark)
python CompareThreeApproaches.py
```

Important files to inspect when debugging or changing behavior:
- `ComputationalGraphs/Core/Graph.py` – core Graph class and node orchestration
- `ComputationalGraphs/Core/GraphProcessor.py` – execution engine (concurrent & forward processing)
- `ComputationalGraphs/Core/MLPGraph.py` – MLP implementation (concurrent, buffers)
- `ComputationalGraphs/Core/MLPGraphForwardProcessing.py` – MLP (forward processing)
- `ComputationalGraphs/Core/BackpropGraph.py` and `BackpropGraphForwardProcessing.py` – backprop implementations
- `ComputationalGraphs/Nodes/ContainerNode.py` – trainable parameter container
- `ComputationalGraphs/Nodes/BufferNode.py` – timing buffers used by concurrent mode
- `.github/copilot-instructions.md` – longer agent instructions and research context

Coding and edit guidelines for assistants:
- Make minimal, targeted edits. Prefer fixing root causes but avoid sweeping refactors.
- Preserve the node-centric design: nodes are active computational actors; keep their responsibilities local.
- Do not change buffer size formulas or synchronization timing without running tests and understanding the effect.
- When touching forward-processing code, ensure source nodes and `ContainerNode`s are marked processed for the first pass (see `PrepareForForwardProcessing`).
- Use existing naming conventions for weights (e.g., `W_x0H0N1`) when accessing/setting node values programmatically.
- Run small tests after edits: `ClassicMLPTestOnXOR.py` and `CompareThreeApproaches.py` are quick sanity checks.

What to do before making larger changes:
- Propose design changes in an issue or PR description and get confirmation before implementing core execution-model edits.
- Add or update tests that exercise the changed behavior.

If you need more context, read `.github/copilot-instructions.md` for the research thesis and detailed architecture notes.
