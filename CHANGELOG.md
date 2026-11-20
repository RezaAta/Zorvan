# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Docs: added the accepted Phase 0 processing semantics, Python node catalog, and versioned IR proposal, with `.cgjson` mapping notes and documentation for the Windows GUI-test skips.
- Tooling: added a Python-reference conformance trace recorder and generated cases for 43 built-in node kinds, all 13 GUI examples, and standalone ANFIS XOR; removed the duplicate `Graph.AbstractNodes` definition and two explicitly dead files.
- Benchmarks: added an initial XOR MLP comparison and graph/hidden-width scaling runs; documented workload differences and the unverified historical 3.91× figure.
- Refactor: moved the Python implementation, GUI and tests into `reference/`, renamed its import package to `zorvan_reference`, and updated packaging, CI, launch and release paths.
- Fix (core): `CompressedNode` and `AbstractNode` now follow snapshot semantics under all processors. They gather their internal nodes' inputs in Phase 1 and only compute in Phase 2, so compressing or abstracting nodes no longer changes per-tick results or makes them depend on processing order. `CompressedNode` no longer forces batch processing on its internal nodes, and `AbstractNode` processes internal nodes sequentially instead of in a per-tick thread pool. Covered by `reference/Tests/core/graph/test_complex_node_snapshot_semantics.py`.
- GUI: removed research-specific demo examples from the Examples menu; a curated example set will replace them. Tests that used them as fixtures now build neutral graphs.
- Docs: added `docs/REARCHITECTURE_PLAN.md` (roadmap toward a Rust engine with TypeScript/Tauri clients, execution-semantics refinements, decision log).
- Docs: refreshed the README, agent instructions, contributor guides and GUI docs (current paths, processing-mode status, removed references to missing scripts), rewrote `docs/ARCHITECTURE_COMPARISON.md`, and marked `docs/gui_rebuild/` as an archived record.
- Tooling: agentic-development setup. `AGENTS.md` is the single agent guide (merging the former `docs/COPILOT_README.md` and `docs/AGENT_POLICY.md`); `CLAUDE.md` imports it; `.claude/settings.json` requires approval for git writes; `.github/copilot-instructions.md` points to `AGENTS.md`; `scripts/run_checks.ps1` runs the core suite by default (`-All` for everything).
- CI: the Windows executable workflow publishes a GitHub Release only for `v*` tag pushes (other runs upload a workflow artifact only) and has `contents: write` permission.

## v0.1.0

- Refactor: renamed Python package from `ComputationalGraphs` to `zorvan` and updated all imports and documentation accordingly.

- Release: Added Zorvan public release assets and governance baseline (`LICENSE`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, issue templates).
- Release: Added curated export tooling (`scripts/export_zorvan_release.ps1`) and a scope definition (`RELEASE_SCOPE_ZORVAN.md`, kept outside the public tree).
- Release: Stabilized the CI workflow for public launch and added a publish guide (`PUBLISH_ZORVAN.md`, kept outside the public tree).
- Release: Added Windows executable packaging, release workflow, and app icon.

- GUI: Added a numeric speed input (ms/step) `QSpinBox` in the control panel to type the processing speed directly. The numeric input is synced with the existing speed slider and label.
- GUI: Added copy/cut/paste support in the canvas (keyboard shortcuts: Ctrl+C, Ctrl+V, Ctrl+X). Copy/paste copies visual node items and recreates internal edges between copied nodes. Pasted nodes are centered in the current view and selected.
- GUI: Added Copy/Cut/Paste actions in the Edit menu with standard shortcuts.
- GUI: Fixed an AttributeError on startup by replacing `QKeySequence.Copy|Cut|Paste` with `QKeySequence.StandardKey.Copy|Cut|Paste`.

- GUI: Added quick Multi-Node Connect UX. When multiple nodes are selected, hover the outer edge of any selected node to preview a multi-connection and drag to connect all selected nodes to a target node. (Preview, highlight and preview lines implemented.)
- GUI: Added an automated GUI test to verify multi-node connection behavior.
- GUI: Added grid and snapping features to the canvas.
  - Added an optional background grid with two modes: `Node cell (1x1)` and `Node 4x4` (default)
  - Added `Snap to Grid` with optional `Snap while dragging` and `Snap Granularity` (grid cell vs node block)
  - Grid display and snapping are toggleable from the Visualization panel. Grid rendering is optimized to draw only the visible area.

- GUI: Introduced `ThemeMixin` helper to centralize theme application and simplify widget updates; migrated `NodePalette` to use `ThemeMixin` and added a test to verify theme updates.
- GUI: Removed debug prints and modal debug dialogs from "Connect to Self" (context menu); replaced with non-intrusive logging and transient status messages, with a test asserting no modal debug dialogs are shown during connect/disconnect.
- GUI: Fixed GUI startup crash, theme/apply handling, plot adapter defaults and toolbar; cleaned up legacy GUI tests.
- Core: Removed unused `computationTime` and `computationStructure` helpers from node classes and related setter methods to simplify node internals, with a test asserting no external dependency on these helpers.
