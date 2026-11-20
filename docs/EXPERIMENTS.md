## Experiments — Purpose and Conventions

Experiments are scientific or comparative procedures and scripts used to validate, benchmark, or explore behavior of models, algorithms, or system designs. They are NOT unit or integration tests and should not be treated as such.

Key conventions
- **Purpose**: Investigate and report; may be exploratory, long-running, or require plotting and manual inspection.
- **Location**: Place experiments under a top-level `Experiments/` directory (create it when needed; it isn't in the public tree yet), or in `reference/zorvan_reference/Examples/` when tied directly to a user-facing example. Performance benchmarks will live in `benchmarks/` (see `docs/REARCHITECTURE_PLAN.md`, Phase 0).
- **Naming**: Prefer prefixing filenames with `exp_` (e.g., `exp_my_experiment.py`) and avoid names that start with `test_` or match pytest collection patterns to prevent accidental test discovery.
- **Reproducibility**: Include a clear runner (example: `run.py` or `README.md`) with seed control and instructions to reproduce results.
- **CI**: Experiments are not executed as part of the standard `pytest` suite. If you want specific quick checks in CI, implement them as dedicated `reference/Tests/` test cases.

Recommended structure

Experiments/MyExperiment/
- run.py                # reproducible runner (example entry point)
- README.md             # rationale, dataset, how to run
- output/               # generated plots, CSV summaries (ignored by CI)

If an experiment becomes a maintained benchmark or a deterministic verification for behavior customers rely on, consider extracting the deterministic, quick checks into `reference/Tests/` as proper test cases.

See `DEVELOPER_GUIDE.md` and `CONTRIBUTING.md` for links to this convention.
