# Zorvan Public Release Plan

This plan assumes the current branch `MVVM-UI-Migration` is the most up-to-date source.

## Goal

Release a clean public repository as **Zorvan** with curated history, MIT license, and stable CI.

## Phase 1 — Freeze and Curate

1. Create a release branch from current state:
   - `git checkout MVVM-UI-Migration`
   - `git pull`
   - `git checkout -b release/zorvan-v0.1.0`
2. Define inclusion scope for v0.1.0:
   - Keep: `zorvan/`, `Examples/`, `Experiments/`, core docs, setup files.
   - Exclude: debug logs, heavy artifacts, local repro outputs, temporary scripts.
3. Remove or archive non-release files from tracked content.

## Phase 2 — Sanitize

1. Search and remove local absolute paths and personal machine references.
2. Ensure `.gitignore` excludes logs, artifacts, dumps, and local env folders.
3. Validate no sensitive files remain in tracked tree.

## Phase 3 — Rebrand to Zorvan

1. Update public-facing naming:
   - `README.md` title and description
   - package metadata (`setup.py`, optional `pyproject.toml` project section)
   - docs with old repository URLs/placeholders
2. Keep internal Python import paths stable for v0.1.0 unless full package rename is planned.
3. Add migration note: "Project released publicly as Zorvan."

## Phase 4 — Community and Governance

Required baseline files:

- `LICENSE` (MIT)
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `SUPPORT.md`
- `.github/ISSUE_TEMPLATE/*`

## Phase 5 — Quality Gate

1. Run targeted tests first, then full suite:
   - `pytest -q Tests/core/graph/test_sequence_finder.py`
   - `pytest -q`
2. Run GUI smoke test:
   - `python run_new_ui.py`
3. Ensure GitHub Actions CI passes on release branch.

## Phase 6 — New Public Repository Creation

1. Create new GitHub repo: `zorvan`.
2. Push curated release branch there as `main` with a fresh/squashed history:
   - Option A (recommended): export curated tree and initialize new git history.
   - Option B: mirror selected commits if strict provenance is required.
3. Configure repository settings:
   - Branch protection on `main`
   - Require PR + passing checks
   - Enable Security Advisories

## Phase 7 — Release v0.1.0

1. Update `CHANGELOG.md` with v0.1.0 notes.
2. Tag and publish:
   - `git tag -a v0.1.0 -m "Zorvan v0.1.0"`
   - `git push origin v0.1.0`
3. Create GitHub Release with:
   - Highlights
   - Known limitations
   - Upgrade/migration notes

## Execution Notes

- Keep this repository as private/archive reference after Zorvan launch.
- Use `MVVM-UI-Migration` as the source of truth during curation.
- Do not rename core internal modules in the same release unless required; keep risk low for v0.1.0.
