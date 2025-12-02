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
6. Push the branch and open a PR with a short TL;DR message and the checklist completed.

## Test Templates

See `Tests/templates/` for test template skeletons.

## CI and Checks

CI is advisory by default; keep an eye on the CI checks and address issues proactively. Critical checks (tests) may become required later. The CI workflow reports linting, commit checks, and tests on PRs.
