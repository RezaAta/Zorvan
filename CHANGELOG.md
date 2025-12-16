# Changelog

All notable changes to this project will be documented in this file.

## Unreleased (PyQTUI)

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
(End of changes)
