PROPOSED TEST REMOVALS / RELOCATIONS
====================================

Generated: 2026-05-22

Purpose
-------
This document lists tests that look obsolete, brittle, or depend on removed resources. These are *proposals* only — do not delete files without review. For each candidate I list: path, reason, and recommended action.

1) Tests/check_initial_pop_same.py
- Reason: Imports and executes an `Experiments/exp_graph_ea_dejong_sphere.py` script that is missing in this workspace. The test currently must be skipped at collection-time (we patched it to skip). If the experiment was intentionally removed, the test is now orphaned.
- Recommendation: Remove this test or replace it with a focused unit test that exercises the EA initialization routine directly (not via an external example runner). If you want to keep behavioral comparison, move the example into `Tests/fixtures/` and import deterministically.

2) Tests/gui_tests/integration/test_visual_regression.py
- Reason: Requires baseline images stored in `Tests/baselines/` and Pillow; brittle and heavy (screenshot comparison). Baselines are large binary artifacts and often diverge between platforms.
- Recommendation: Move to an optional `visual-regression/` folder and exclude from default CI runs. Keep it runnable locally for manual checks. Add a CI job or nightly workflow that runs these with a pinned image baseline artifact store.

3) Tests/gui_tests/integration/test_examples_loader_screenshot.py and related screenshot tests
- Reason: Tests that capture GUI screenshots and compare them are fragile and require external assets and Pillow. If baselines or helper scripts change, these tests fail.
- Recommendation: Same as (2) — move to optional visual-regression suite or gate them behind an environment flag (e.g., `VISUAL_REGRESSION=1`).

4) GUI rendering / integration tests flagged as high-flakiness
- Candidate files (review before action):
  - Tests/gui_tests/integration/test_canvas_rendering.py
  - Tests/gui_tests/integration/test_plot_views.py
  - Tests/test_combined_node_palette_rendering.py
  - Tests/test_combined_node_palette_paint_no_error.py
  - Tests/gui_tests/integration/test_plot_view_smoke.py
- Reason: These tests depend on pixel rendering, event timing, or 3rd-party backends (matplotlib / pyqtgraph) and are flaky on CI or different platforms.
- Recommendation: Mark them as `@pytest.mark.flaky` or `skipif` unless `VISUAL_REGRESSION` env var is set. Alternatively, rewrite to verify internal state or component outputs (data structures) instead of screenshots.

5) Legacy/duplicate tests referencing `zorvan.GUI` vs `gui_framework`
- Notes: The codebase contains both `zorvan.GUI` modules and a newer `gui_framework` package. Many tests exercise the older API or both packages. If `zorvan.GUI` is being deprecated, tests should be migrated, not kept duplicative.
- Recommendation: Produce a migration plan (not automatic removal). Any tests that exist only to validate legacy code you plan to delete can be listed for removal after the corresponding code is removed.

General cleanup rules I followed to propose candidates
- Tests referencing missing files or external artifact baselines are high-priority removal/migration candidates.
- GUI screenshot / visual-regression tests are brittle and should be optional (kept but excluded from default CI).
- Do not delete tests purely because they import `zorvan.GUI` — only when the underlying code is being removed.

Next steps (suggested)
1. Review the above candidates and confirm which to (a) remove, (b) relocate to `visual-regression/`, or (c) migrate to unit-style tests.
2. For each approved removal, I'll prepare a PR that: moves files to `archive/tests/` (instead of immediate deletion), updates `pytest.ini` to exclude visual-regression by default, and documents the change in `PROPOSED_TEST_REMOVALS.md`.
3. Optionally, I can try running the GUI test suite with `QT_QPA_PLATFORM=offscreen` and a pinned Pillow install to identify concrete failures for the remaining GUI tests.

If you'd like, I can now prepare the PR that moves the visual regression tests into an `optional/visual-regression/` folder and updates `pytest.ini` to exclude them by default. Otherwise tell me which of the candidates above you approve for removal/relocation.
