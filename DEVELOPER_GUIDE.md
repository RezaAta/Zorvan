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

## Solo Developer Branching Guidance

If you are primarily working alone on this repository, you can adopt the following simplified branching strategy:

- Use the current branch (e.g., `PyQTUI`) for tiny changes such as typos, small documentation updates, or single-line code fixes.
- For feature work, large refactors, or experimental changes, create a new topic branch with a descriptive name.
- Keep commits focused and small. When merging large work into `PyQTUI` or `main`, consider squashing the topic branch or rebasing and cleaning up commit history.
- Delete branches once they are merged to keep the repository tidy. If you need to preserve a branch as an archive for reference, consider pushing it to `origin/<name>` with a clear note in the PR body.

This gives you the conveniences of a single-branch workflow for quick edits while preserving the safety and structure of branching for larger changes.

## CI and Checks

CI is advisory by default; keep an eye on the CI checks and address issues proactively. Critical checks (tests) may become required later. The CI workflow reports linting, commit checks, and tests on PRs.
