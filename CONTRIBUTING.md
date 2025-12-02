# Contributing to ComputationalGraphs

Thanks for contributing! This project uses a set of policies and tools to keep code quality high and a predictable workflow. Follow the steps below to make your contribution smooth and consistent.

## High-level Guidance

- Follow TDD (Test-Driven Development): Write a failing test that demonstrates desired behavior or the bug, then implement the minimal code to satisfy the test, and refactor afterwards.
- Keep changes small: Make one contextual change per commit. If a change requires multiple pieces (e.g., code + tests + docs), put each logical change into its own commit.
- Use Conventional Commits via Commitizen: `feat:`, `fix:`, `chore:`. See below for usage.
- Clean code principles: Apply Uncle Bob’s clean code best practices: readable names, small functions, single responsibility, and clear tests.

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
