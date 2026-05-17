# Zorvan v0.1.0 Release Scope

This file defines what should be exported from `MVVM-UI-Migration` into the public `zorvan` repository.

## Include (public)

- `zorvan/`
- `scripts/`
- `docs/`
- `.github/workflows/`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/`
- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `SUPPORT.md`
- `requirements.txt`
- `requirements_dev.txt`
- `requirements_gui.txt`
- `pytest.ini`
- `pyproject.toml`
- `setup.py`
- `run_new_ui.py`
- `PUBLISH_ZORVAN.md`
- `RELEASE_SCOPE_ZORVAN.md`
- `ZORVAN_RELEASE_PLAN.md`

## Exclude (private/dev-only)

- `artifacts/`
- `__pycache__/`
- `.venv/`, `.venv_old/`
- `*.log`, `*.dmp`, `*.stackdump`
- local repro outputs and ad-hoc temporary files

## Decision Notes

- Internal import/package path names are now `zorvan` (updated before v0.1.1).
- Public project/repository identity is `Zorvan`.
- Source branch for export: `MVVM-UI-Migration`.
