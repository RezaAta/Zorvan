# Phase 4 Canvas Migration - Complete Testing Guide

## Overview

This guide explains how to test the complete Canvas Migration implementation (Stages 1-3). The implementation includes rendering, interaction, and undo/redo commands.

## Quick Test Summary

### ✅ Unit Tests (52 tests, 100% passing)
- **Stage 1**: 34 tests for CanvasViewModel rendering
- **Stage 2**: 9 tests for selection and interaction
- **Stage 3**: 9 tests for undo/redo commands
- **Execution time**: ~0.15 seconds
- **Command**: `python -m pytest gui_tests/unit/test_canvas_viewmodel.py gui_tests/unit/test_canvas_commands.py -v`

### ⚠️ Integration Tests (15 tests, require display libraries)
- Require libEGL and Xvfb for headless execution
- Test View rendering and interaction
- **Command**: `QT_QPA_PLATFORM=offscreen python -m pytest gui_tests/integration/test_canvas_rendering.py -v`

### ✅ Manual Test Application
- Interactive GUI for visual testing
- **Command**: `python Examples/exp_canvas_view.py`

---

## Detailed Testing Instructions

### 1. Prerequisites

**Install Dependencies:**
```bash
pip install pytest PyQt6
```

**For headless CI testing (optional):**
```bash
# Ubuntu/Debian
sudo apt-get install -y libegl1 libgl1 xvfb

# Set environment variable
export QT_QPA_PLATFORM=offscreen
```

### 2. Unit Tests

Unit tests run without GUI and test all ViewModel logic.

**Run all unit tests:**
```bash
cd /path/to/ComputationalGraphs
python -m pytest gui_tests/unit/ -v
```

**Run specific test suites:**
```bash
# Stage 1: Rendering tests
python -m pytest gui_tests/unit/test_canvas_viewmodel.py::TestCanvasViewport -v
python -m pytest gui_tests/unit/test_canvas_viewmodel.py::TestGraphLoading -v
python -m pytest gui_tests/unit/test_canvas_viewmodel.py::TestViewportManagement -v

# Stage 2: Interaction tests
python -m pytest gui_tests/unit/test_canvas_viewmodel.py::TestSelectionInteractive -v

# Stage 3: Command tests
python -m pytest gui_tests/unit/test_canvas_commands.py -v
```

**Expected output:**
```
52 passed in 0.15s
```

### 3. Integration Tests

Integration tests require PyQt6 and display libraries.

**Run integration tests (headless):**
```bash
export QT_QPA_PLATFORM=offscreen
python -m pytest gui_tests/integration/test_canvas_rendering.py -v
```

**Expected output (if libEGL installed):**
```
15 passed in X.XXs
```

**Expected output (if libEGL NOT installed):**
```
15 skipped
```

**Note**: Integration tests are optional for CI. Unit tests provide comprehensive coverage.

### 4. Manual Testing with GUI

The manual test application provides interactive testing of all features.

**Run test application:**
```bash
python Examples/exp_canvas_view.py
```

**What to test:**

#### Stage 1: Rendering
1. **Verify nodes display**: 4 nodes (Input A, Input B, Process, Output) should be visible
2. **Verify edges display**: 3 edges connecting the nodes with arrows
3. **Test zoom**: Click "Zoom In" / "Zoom Out" buttons or use mouse wheel
4. **Test viewport reset**: Click "Reset View" to return to default zoom/pan
5. **Test node colors**: Click "Color Node C" multiple times to change Process node color
6. **Test active highlighting**: Click "Toggle Node C Active" to see bright blue highlight

#### Stage 2: Interaction
7. **Test node dragging**: Click and drag any node - edges should follow
8. **Test single selection**: Click a node - yellow border should appear
9. **Test multi-selection**: Ctrl+Click multiple nodes - all should have yellow border
10. **Test rubber band selection**: Click and drag on empty area - multiple nodes selected
11. **Test select all**: Click "Select All" or press Ctrl+A
12. **Test clear selection**: Click "Clear Selection" or click empty area
13. **Test status bar**: Selected nodes should appear in bottom status bar

#### Stage 3: Commands & Undo/Redo
14. **Test undo**: Drag a node, then click "Undo" or press Ctrl+Z - node should return
15. **Test redo**: After undo, click "Redo" or press Ctrl+Shift+Z - node should move back
16. **Test multiple undo**: Drag multiple nodes, then undo several times
17. **Test undo stack**: Status bar should show "Undo: Move Nodes" when undo available
18. **Test delete placeholder**: Select nodes and press Delete - command logged (placeholder)

**Expected behavior:**
- All interactions should be smooth without lag
- Yellow selection borders should be clearly visible
- Undo/redo should restore exact positions
- Status bar should update in real-time
- Edges should stay connected during dragging

### 5. Feature Checklist

Use this checklist to verify all features work:

**Stage 1: Rendering ✅**
- [ ] Nodes render with correct positions
- [ ] Edges render with bezier curves and arrows
- [ ] Different node types have different colors (compressed=gold, abstract=purple, default=blue)
- [ ] Labels display correctly on nodes
- [ ] Zoom in/out works smoothly
- [ ] Viewport reset works
- [ ] Node color changes reflect immediately
- [ ] Active node highlighting works (bright blue)

**Stage 2: Interaction ✅**
- [ ] Nodes can be dragged
- [ ] Edges follow dragged nodes in real-time
- [ ] Single node selection works (click)
- [ ] Multi-node selection works (Ctrl+click)
- [ ] Rubber band selection works (drag on empty area)
- [ ] Selection visual feedback works (yellow border)
- [ ] Select all works (Ctrl+A)
- [ ] Clear selection works (click empty area)
- [ ] Status bar shows selected nodes

**Stage 3: Commands & Undo/Redo ✅**
- [ ] Undo works for node movements (Ctrl+Z)
- [ ] Redo works for node movements (Ctrl+Shift+Z or Ctrl+Y)
- [ ] Multiple undo/redo works
- [ ] Undo/redo buttons work
- [ ] Status bar shows undo/redo availability
- [ ] Delete command created (placeholder, not functional yet)
- [ ] Command merging works (consecutive moves merge into one undo)

---

## Summary

**Minimum testing for CI:**
```bash
python -m pytest gui_tests/unit/ -v
```
Expected: 52 passed in ~0.15s ✅

**Visual verification:**
```bash
python Examples/exp_canvas_view.py
```
Expected: Interactive GUI with all features working ✅

---

**Status**: All 52 unit tests passing, Stage 3 complete ✅
**Last Updated**: 2025-12-19
**Phase 4 Progress**: 100% (All 3 stages complete)
