# Zorvan

Zorvan is a visual framework for building, running and combining AI models as
computational graphs. Every operation (an addition, an activation function, a
fuzzy membership function, a crossover operator) is a node. Neural networks,
fuzzy inference systems, evolutionary algorithms and their hybrids are built by
wiring nodes together.

Because models share the same building blocks, they can be combined at any
level:
- **Fusion hybrids** change a model's internals, for example an MLP layer that
  mixes different activation functions, or ANFIS. You rewire nodes instead of
  reimplementing models.
- **Modular hybrids** connect whole models, for example a neural predictor
  feeding a fuzzy controller.

The graph is also the user interface, so the design you see is the model that
runs.

> Status: v0.1.0, Python engine with a PyQt6 editor. A faster Rust engine with
> desktop and web clients is planned: see the
> [re-architecture plan](docs/REARCHITECTURE_PLAN.md).

## Key concepts

- **Nodes and ordered inputs.** A node computes its value from its
  predecessors' values (and optionally the time step). Input order follows the
  order connections were made, and it matters.
- **Processing modes.**
  - *Concurrent* (main mode): every tick, all nodes read a snapshot of the graph,
    then all update. Results don't depend on processing order, and a signal
    advances one node per tick.
  - *Forward*: nodes run along data dependencies (experimental).
  - *Manual*: you choose the execution sequence (experimental).
- **Batching.** Nodes process inputs in batches up to their capacity, either
  inclusively (carrying the running result) or exclusively.
- **Simplification.** Large graphs can be shown at coarser granularity:
  - chains collapse into compressed nodes;
  - groups of parallel nodes collapse into abstract nodes.

  This is reversible and doesn't change results.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements_gui.txt
pip install -e .
```

Or use the bootstrap script: `.\scripts\bootstrap.ps1 -InstallGui`
(`./scripts/bootstrap.sh --gui` on Linux/macOS).

## Quick start

```powershell
# Run the visual editor
python run_new_ui.py

# Optional flags: auto-load an example, start maximised, debug logging
python run_new_ui.py --example "<example name>" --maximize --debug
```

### Example scripts

`zorvan/Examples/` contains demo scripts (not automated tests). They adjust
`sys.path` themselves, so they run from any directory:

```powershell
python zorvan/Examples/FibonacciExample.py
python zorvan/Examples/ANFIS_XOR_Train_Concurrent.py
```

### Windows executable

```powershell
.\scripts\build_exe.ps1
```

The build uses `assets/zorvan.ico` for both the executable and the window icon.
GitHub Actions (`.github/workflows/build_windows_exe.yml`) builds
`dist\ZorvanNewUI.exe` on every run and uploads it as a workflow artifact. It
publishes a GitHub Release only when a `v*` tag is pushed.

## Documentation

- **[Re-architecture plan](docs/REARCHITECTURE_PLAN.md)**: roadmap, execution semantics, decision log
- **[GUI README](docs/GUI_README.md)**: visual editor features and usage
- **[Examples features](docs/EXAMPLES_FEATURES.md)**: built-in example graphs and MLP/backprop tools
- **[Architecture comparison](docs/ARCHITECTURE_COMPARISON.md)**: concurrent vs forward MLP architectures
- **[Plotting](docs/PLOTTING_FEATURE.md)**: live plotting of node values
- **[Developer guide](docs/DEVELOPER_GUIDE.md)**: setup, TDD, pre-commit, commit conventions
- **[Contributing](CONTRIBUTING.md)**: contribution rules
- **[Agent guide](AGENTS.md)**: rules and project map for AI coding agents
- **[GUI rebuild archive](docs/gui_rebuild/)**: record of the PyQt MVVM migration

## Development

Run `scripts/run_checks.ps1` to validate changes locally (core tests by default;
`-All` for the full suite), and see `CONTRIBUTING.md` for the rules. AI agents
follow `AGENTS.md` (`CLAUDE.md` imports it for Claude Code). Release steps are in
`ZORVAN_RELEASE_PLAN.md`.

## License

MIT, see [LICENSE](LICENSE).
