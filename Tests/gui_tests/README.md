# GUI Test Suite

This directory contains the GUI-oriented pytest suite for the ComputationalGraphs project.

## Structure

- `integration/` - higher-level UI workflows, dialog flows, and headless main window integration tests.
- `unit/` - feature-focused tests for viewmodels, adapters, controllers, and isolated Qt widget behavior.

## Goals

- Keep `integration/` tests focused on full UI flows and cross-component interaction.
- Keep `unit/` tests focused on small feature areas and isolated behavior.
- Use dedicated feature directories in `unit/` to reduce the flat namespace and improve discoverability.
- Preserve shared Qt fixtures in `unit/conftest.py` and avoid repeated `QApplication` setup.

## Future cleanup guidance

- Add new component tests under feature-specific subdirectories in `unit/`.
- When a test exercises multiple dialogs or the main window, prefer `integration/`.
- Use `pytest.mark.integration` for longer-running or headless UI flow tests.

## Integration categories

The integration test tree is organized by feature area:

- `ann/` for ANN and MLP colorization persistence workflows
- `canvas/` for canvas rendering and visualization flows
- `dialogs/` for dialog-based UI flows
- `examples/` for example loader and main-window example interactions
- `inspector/` for inspector panel and node inspector flows
- `plot/` for plot-related integration scenarios
- `startup/` for smoke and main window startup tests
