# GUI Integration Test Organization

Integration tests in this directory cover broader UI workflows that cross-dialog and main window boundaries.

## Categories

- `ann/` - ANN colorization, MLP generation persistence, and related model visualization regression flows.
- `canvas/` - Canvas rendering and canvas-specific integration scenarios.
- `dialogs/` - Full dialog flow tests for dialog widgets such as Backprop, MLP generation, and New Graph.
- `examples/` - Example loader and main-window example load behavior.
- `inspector/` - Inspector panel and node inspector integration tests.
- `plot/` - Plot view, plot configuration, and PlotWindow compatibility tests.
- `startup/` - Smoke and main-window startup scenarios.

## Intent

- Validate full-feature flows such as example loading, dialog interactions, cluster workflows, and inspector integration.
- Keep widget-level smoke tests and cross-component UI flows in `integration/`, while preserving pure viewmodel or adapter tests in `Tests/gui_tests/unit/`.
- Use headless/offscreen mode when possible so the tests can run in CI without a display.

## Guidelines for new integration tests

- Prefer `integration/<feature>/` when the test exercises multiple UI components or the main application window.
- Keep `integration/` tests focused on behavior, not implementation details.
- Use the shared `QApplication` fixture and `pytest.mark.skipif` for platform-specific dependencies.
- If a test is purely a viewmodel or adapter interaction, place it under `Tests/gui_tests/unit/` instead.
