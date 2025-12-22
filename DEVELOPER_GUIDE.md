# Developer Guide

This guide provides a concise overview for contributors and agents working on this repository. It complements `CONTRIBUTING.md` and `AGENT_POLICY.md`.

## Key Practices

- TDD: Write tests first, then implement. Keep tests focused and deterministic.
- Commit Discipline: One logical change per commit, with proper Conventional Commit messages using `cz` (commitizen).
- Clean Code: Keep functions short, names descriptive, avoid deep nesting, and prefer small, composable building blocks.

## Local Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# optional test dependencies or dev packages
pip install -r requirements_dev.txt || pip install pytest pre-commit commitizen
```

### One-step Bootstrapping
To simplify environment setup you can use the included `scripts/bootstrap` helpers:
Windows PowerShell:
```powershell
.\scripts\bootstrap.ps1
# To include GUI requirements too:
.\scripts\bootstrap.ps1 -InstallGui
```
UNIX / macOS:
```bash
./scripts/bootstrap.sh
# To include GUI requirements too:
./scripts/bootstrap.sh --gui
```

### GUI (optional)
If you plan to run the GUI tests or use the graphical interface, install the GUI requirements:

```powershell
pip install -r requirements_gui.txt
```

For running GUI tests in CI without a display, Xvfb is used by the CI job, or on your local machine you can run tests directly if you have a desktop environment (or use a virtual display such as Xvfb on Linux).

## Running Tests

```powershell
pytest -q
```

## Formatting/Linting (pre-commit)

```powershell
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Quick Workflow

1. Branch from `main` (or `PyQTUI` if that's your working branch).
2. Create failing tests demonstrating the desired behavior.
3. Implement minimal changes to satisfy tests.
4. Run tests and `pre-commit` hooks locally.
5. Use `git cz` to create structured commits; split logical changes into separate commits.
5. Push the branch and ensure local CI/test smoke-runs succeed; since this repository is maintained in a solo-developer mode, opening a PR is optional and not required for day-to-day fixes—commit directly after tests and documentation are updated.

### Experiments vs Tests

- **Tests:** short, deterministic, and automated assertions that verify program behavior. Place tests under `Tests/` or `ComputationalGraphs/Tests/` and run them with `pytest`.
- **Experiments:** long-running or exploratory scripts used for scientific comparisons, plotting, or benchmarking. Place experiments under `Experiments/` (or `Examples/` when tightly coupled to an example). Prefer prefixing such scripts with `exp_` (e.g., `exp_my_experiment.py`) to make them easy to find and to avoid pytest collection. Experiments are not part of the automated `pytest` run by default; see `EXPERIMENTS.md` for conventions.

## Test Templates

See `Tests/templates/` for test template skeletons.

## Solo Developer Branching Guidance

This repository supports a solo-developer workflow focused on rapid iteration for bug fixes and migration work. The updated policy is:

- The **new UI replaces the legacy UI** and we prioritize restoring feature parity and fixing regressions over adding new features.
- For small fixes (bugs, docs, tests), you may commit directly to the primary working branch after verifying tests and updating docs — **PRs are optional and not required** for solo work.
- For larger, risky refactors or experimental work, create a topic branch with a descriptive name and keep changes small and well-tested; when ready, merge into the main branch following your normal commit hygiene.
- Keep commits focused and small; squash or rebase large topic branches before merging to keep history readable.
- Delete topic branches once merged to keep the repository tidy; if you need to preserve a branch for reference, push it with a clear note.

This gives you the convenience of a single-developer workflow where speed and stability are primary, while still encouraging tests and clear documentation for each change.

## CI and Checks

CI is advisory by default; keep an eye on the CI checks and address issues proactively. Critical checks (tests) may become required later. The CI workflow reports linting, commit checks, and tests on PRs.
