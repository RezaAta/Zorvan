# Changelog

All notable changes to this project will be documented in this file.

## Unreleased (PyQTUI)

- Refactor: renamed Python package from `ComputationalGraphs` to `zorvan` and updated all imports and documentation accordingly.  This will become part of v0.1.1.

- Release: Added Zorvan public release assets and governance baseline (`LICENSE`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, issue templates).
- Release: Added curated export tooling (`scripts/export_zorvan_release.ps1`) and scope definition (`RELEASE_SCOPE_ZORVAN.md`).
- Release: Stabilized CI workflow for public launch and added publish guide (`PUBLISH_ZORVAN.md`).

- GUI: Added a numeric speed input (ms/step) `QSpinBox` in the control panel to type the processing speed directly. The numeric input is synced with the existing speed slider and label.
- GUI: Added copy/cut/paste support in the canvas (keyboard shortcuts: Ctrl+C, Ctrl+V, Ctrl+X). Copy/paste copies visual node items and recreates internal edges between copied nodes. Pasted nodes are centered in the current view and selected.
- GUI: Added Copy/Cut/Paste actions in the Edit menu with standard shortcuts.
- GUI: Fixed an AttributeError on startup by replacing `QKeySequence.Copy|Cut|Paste` with `QKeySequence.StandardKey.Copy|Cut|Paste`.

- GUI: Added quick Multi-Node Connect UX. When multiple nodes are selected, hover the outer edge of any selected node to preview a multi-connection and drag to connect all selected nodes to a target node. (Preview, highlight and preview lines implemented.)
- GUI: Added automated GUI test `Tests/test_multi_connection_gui.py` to verify multi-node connection behavior.
 - GUI: Added grid and snapping features to the canvas.
 	- Added an optional background grid with two modes: `Node cell (1x1)` and `Node 4x4` (default)
	 - Added `Snap to Grid` with optional `Snap while dragging` and `Snap Granularity` (grid cell vs node block)
	 - Grid display and snapping are toggleable from the Visualization panel. Grid rendering is optimized to draw only the visible area.

- GUI: Introduced `ThemeMixin` helper to centralize theme application and simplify widget updates; migrated `NodePalette` to use `ThemeMixin` and added `Tests/test_node_palette_theme.py` to verify theme updates.
- GUI: Remove debug prints and modal debug dialogs from "Connect to Self" (context menu); replaced with non-intrusive logging and transient status messages. Added `zorvan/Tests/test_connect_to_self.py` to assert no modal debug dialogs are shown during connect/disconnect.
- Core: Removed unused `computationTime` and `computationStructure` helpers from node classes and related setter methods to simplify node internals; added `zorvan/Tests/test_basicnode_cleanup.py` to assert no external dependency on these helpers.
(End of changes)
