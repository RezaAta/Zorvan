# Zorvan Release Plan

## Status

**v0.1.0 has been released** (tag `v0.1.0`; public repository
`github.com/RezaAta/Zorvan`, default branch `main`). The original launch plan,
which curated a private development branch into this public repository, is
complete:

| Phase | Status |
|-------|--------|
| 1. Freeze and curate | Done (`Zorvan-For-Release` branch) |
| 2. Sanitize | Done, except the items below |
| 3. Rebrand to Zorvan | Done: package renamed `ComputationalGraphs` → `zorvan` |
| 4. Community and governance | Done: `LICENSE` (MIT), `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `.github/ISSUE_TEMPLATE/*` |
| 5. Quality gate | Core tests pass in CI; some Windows-unstable GUI tests are skipped |
| 6. Public repository | Done |
| 7. Release v0.1.0 | Done; the Windows executable is built by `.github/workflows/build_windows_exe.yml` on `v*` tags |

## Remaining cleanup for v0.1.x

- `setup.py`: replace the placeholder URL `https://github.com/ORG_OR_USER/zorvan`.
- Remaining old names in code strings: the application and organisation names
  and the argparse description in `run_new_ui.py` ("Computational Graphs
  Editor"), and the header comment in `requirements_gui.txt`.
- Re-enable or document the skipped Windows GUI tests (commit `ff02e307`).
- Remove dead files: `zorvan/Core/GraphProcessor_optimized_broken.py`,
  `gui_framework/adapters/__init___new.py`.

These overlap with Phase 0 of `docs/REARCHITECTURE_PLAN.md`; do them there if
that phase starts first.

## Releasing a new version

1. Update `CHANGELOG.md`: move the "Unreleased" entries under the new version.
2. Bump the version in `setup.py` and `pyproject.toml` (`[tool.commitizen]`),
   or use `cz bump`.
3. Make sure CI is green on `main`.
4. Tag and push:
   ```powershell
   git tag -a vX.Y.Z -m "Zorvan vX.Y.Z"
   git push origin vX.Y.Z
   ```
5. The tag push triggers the Windows build workflow, which publishes a GitHub
   Release with `ZorvanNewUI.exe`. Edit the release notes to add highlights,
   known limitations and migration notes.

## Future releases

The next major version follows `docs/REARCHITECTURE_PLAN.md`. The current
Python implementation will be tagged `v0.1.0-python` and kept as the reference
before the repository becomes a monorepo (Phase 0).
