# Contributing to ComputationalGraphs

Thanks for contributing! This project uses a set of policies and tools to keep code quality high and a predictable workflow. Follow the steps below to make your contribution smooth and consistent.

## High-level Guidance

- Follow TDD (Test-Driven Development): Write a failing test that demonstrates desired behavior or the bug, then implement the minimal code to satisfy the test, and refactor afterwards.
- Keep changes small: Make one contextual change per commit. If a change requires multiple pieces (e.g., code + tests + docs), put each logical change into its own commit.
- Use Conventional Commits via Commitizen: `feat:`, `fix:`, `chore:`. See below for usage.
- Clean code principles: Apply Uncle Bob’s clean code best practices: readable names, small functions, single responsibility, and clear tests.

## Solo Developer Workflow

If you are working on this repository as a single contributor, we suggest the following convention to keep your workflow simple and the commit history tidy:

- Keep tiny fixes and single-line changes on your current branch (e.g., `PyQTUI`). Small edits include: typos, small README updates, or `.gitignore` additions.
- For anything larger than a trivial edit (feature development, refactors, API changes), create a topic branch (e.g., `feat/<name>` or `refactor/<name>`) to isolate the work and preserve an easy-to-review history.
- Use descriptive Conventional Commits via `git cz` or `cz` for consistent commit messages.
- Before merging big changes into `PyQTUI` or `main`, create a small, single-purpose pull request so CI checks and tests can run.
- Keep branches short-lived: delete the branch after the PR is merged to avoid clutter.

This approach balances the simplicity of working on one branch for tiny changes while preserving the benefits of branching for larger work.

## Commit Messages

We use Conventional Commits. Install commitizen and use `git cz` or `cz` to create structured commit messages.

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for adding or updating tests
- `chore:` for changes to build process or auxiliary tools

Always write a short message; if more details are needed, put them in the body.

## Testing

- The repository uses `pytest`. Run tests locally with:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

- Use the test templates in `Tests/templates/` to scaffold new tests.

### Experiments

If you are running experiments (comparisons, benchmarks, or exploratory scientific runs), place them under `Experiments/` or `Examples/` and follow the guidance in `EXPERIMENTS.md`. Prefer prefixing experiment filenames with `exp_` (e.g., `exp_my_experiment.py`) and avoid `test_` prefixes to prevent accidental collection by `pytest`.

## Pre-commit and Local Checks

This repo supports `pre-commit` hooks to run formatters and linters. Run the following to get them:

```powershell
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

We intentionally keep checks advisory at first; CI will report but not block merges unless configured by maintainers.

## Pull Requests

- Provide a short PR title and a TL;DR (1–2 sentence) summary at the top of the PR description.
- Include links to tests and update docs if behavior changes.
- Ensure that each change is properly split into logical commits.

## Questions

If you are unsure, open an issue or ask maintainers for guidance.
