## Experiments — Purpose and Conventions

Experiments are scientific or comparative procedures and scripts used to validate, benchmark, or explore behavior of models, algorithms, or system designs. They are NOT unit or integration tests and should not be treated as such.

Key conventions
- **Purpose**: Investigate and report; may be exploratory, long-running, or require plotting and manual inspection.
- **Location**: Place experiments under the top-level `Experiments/` directory or in `Examples/` when tied directly to a user-facing example.
- **Naming**: Avoid names that start with `test_` or match pytest collection patterns to prevent accidental test discovery.
- **Reproducibility**: Include a clear runner (example: `run.py` or `README.md`) with seed control and instructions to reproduce results.
- **CI**: Experiments are not executed as part of the standard `pytest` suite. If you want specific quick checks in CI, implement them as dedicated `Tests/` test cases.

Recommended structure

Experiments/MyExperiment/
- run.py                # reproducible runner (example entry point)
- README.md             # rationale, dataset, how to run
- output/               # generated plots, CSV summaries (ignored by CI)

If an experiment becomes a maintained benchmark or a deterministic verification for behavior customers rely on, consider extracting the deterministic, quick checks into `Tests/` as proper test cases.

See `DEVELOPER_GUIDE.md` and `CONTRIBUTING.md` for links to this convention.
