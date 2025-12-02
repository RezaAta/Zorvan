# Real-Time Plotting Feature - Implementation Summary

## Overview
Added a real-time plotting feature to the Computational Graphs GUI that allows users to visualize node values over time during graph execution.

## Features Implemented

### 1. Plot Configuration Dialog (`PlotConfigDialog`)
- **Location**: `ComputationalGraphs/GUI/plot_window.py`
- **Functionality**:
  - Displays list of all nodes in the graph
  - Checkboxes for multi-node selection
  - Max iterations spinner (10-100,000 range, default: 100)
  - OK/Cancel buttons

### 2. Plot Window (`PlotWindow`)
- **Location**: `ComputationalGraphs/GUI/plot_window.py`
- **Functionality**:
  - Matplotlib-based embedded canvas in PyQt6
  - Real-time line plots for multiple nodes
  - Auto-scaling Y-axis (toggleable)
  - Iteration counter display
  - Clear button to reset plot data
  - Automatic color assignment (10 distinct colors cycle)
  - Handles different value types:
    - Numeric values: plotted directly
    - Lists/arrays: averaged (for numeric) or counted (for non-numeric)
    - None values: treated as 0

### 3. Main Window Integration
- **Button Added**: "📊 Open Plot Window" in Controls panel (under Layout section)
- **Method**: `open_plot_window()` in `main_window.py`
- **Auto-update**: Connected to `step_completed` signal
- **Features**:
  - Validates graph exists before opening
  - Warns if no nodes selected
  - Closes previous plot window when opening new one
  - Updates plot on every step/iteration

## Usage Instructions

1. **Load or Create a Graph**
   - Load an example (e.g., "De Jong Sphere Function" EA)
   - Or create your own graph

2. **Open Plot Configuration**
   - Click "📊 Open Plot Window" button in right panel

3. **Configure Plot**
   - Check nodes you want to monitor (e.g., "Fitness", "Population")
   - Set max iterations for X-axis scaling
   - Click OK

4. **Run and Watch**
   - Click "▶ Start" to begin execution
   - Plot updates automatically after each iteration
   - Watch fitness decrease, populations evolve, etc.

5. **Plot Controls**
   - **Clear**: Reset all plot data
   - **Auto-scale Y**: Toggle automatic Y-axis adjustment
   - **Iteration label**: Shows current/max iterations

   ## PyQtGraph Backend

   To improve interactive responsiveness and handle higher-throughput live plotting, a PyQtGraph backend is available as an alternative to the Matplotlib renderer.

   The PyQtGraph backend adds a few UX/quality improvements:
   - White background as the default canvas background for improved contrast and print-ready visuals.
   - Global and per-curve antialiasing (smoother lines) using `pyqtgraph` config options and per-curve antialias flags.
      - Global and per-curve antialiasing (smoother lines) using `pyqtgraph` config options and per-curve antialias flags.
      - New PyQtGraph rendering options: OpenGL toggle, "Decimate Large Data" mode (per-pixel decimation preserving spikes), and optional Gaussian smoothing. These controls are available from the pyqtgraph plot window.
   - Nearest-curve hover tooltips: hovering near a plotted series shows a small tooltip with the nearest curve's name and value (pixel-based proximity threshold).
   - Legend label uniqueness: when multiple nodes share the same name, labels are made unique (e.g., `Name`, `Name (1)`, `Name (2)`).

   You can select the backend in the Controls -> Plotting section under `Plot Backend` dropdown; the default is PyQtGraph when available, otherwise Matplotlib.

   Note: PyQtGraph requires `pyqtgraph` to be installed (e.g., via `pip install pyqtgraph`) and is optional for users who prefer to keep a pure Matplotlib setup.

      Matplotlib: The Matplotlib backend supports hover tooltips using `mplcursors` when the library is installed — fallback behavior works without it.

## Backend selection snippet
To change or force a backend programmatically, use the `create_plot_window()` factory call and set the `backend` parameter: `auto` (default), `pyqtgraph`, or `matplotlib`.

```python
# Force PyQtGraph backend (if installed):
pw = create_plot_window(nodes, max_iterations, parent, backend='pyqtgraph')

# Force Matplotlib backend:
pw = create_plot_window(nodes, max_iterations, parent, backend='matplotlib')

# Let the factory auto-select PyQtGraph when available (default):
pw = create_plot_window(nodes, max_iterations, parent, backend='auto')
```

## Example Use Cases

### Genetic Algorithm (De Jong EA)
- **Plot**: `Fitness` node
- **Expected**: Decreasing fitness values over time
- **Max iterations**: 100-500

### Neural Network Training (XOR MLP)
- **Plot**: `MSE` (loss), `Output` nodes
- **Expected**: Loss decreasing, output converging
- **Max iterations**: 1000-5000

### Fuzzy System
- **Plot**: Temperature input/output nodes
- **Expected**: Smooth transitions between states
- **Max iterations**: 50-100

## Technical Details

### Dependencies
- **PyQt6**: UI framework (already present)
- **matplotlib**: Plotting library (version 3.9.3 verified)
 - **pyqtgraph**: Optional faster plot widget for real-time UI (recommended for many live curves)
- **numpy**: Array handling (used for averaging list values)

### Architecture
- **Signal-based updates**: Uses existing `step_completed` signal
- **Non-blocking**: Plot window runs in separate window (doesn't block main UI)
- **Memory efficient**: Stores only plotted node values, not full graph state
- **Thread-safe**: Updates happen on Qt event loop

### File Structure
```
ComputationalGraphs/GUI/
├── main_window.py         (Modified: added plot button & integration)
├── plot_window.py         (New: PlotConfigDialog & PlotWindow classes)
└── graph_runner.py        (Unchanged: already emits step_completed signal)
```

## Testing

### Test Script
Created `test_plot.py` for quick testing:
- Automatically loads EA example
- Prints usage instructions
- Ready for interactive testing

### Run Test
```bash
cd "c:\My Stuff\Uni & Research\Artificial Inteligence\Computational Graph\Implementations\ComputationalGraphs"
python test_plot.py
```

Or use the regular GUI:
```bash
python run_gui.py
```

## Known Limitations & Future Enhancements

### Current Limitations
1. **X-axis**: Fixed at configuration time (doesn't auto-extend gracefully)
   - Workaround: Extends by 10 when exceeded
2. **Y-axis**: Auto-scale can jump if values vary wildly
3. **No legend repositioning**: Fixed in upper-right
4. **No export**: Can't save plot as image (yet)

### Possible Enhancements
1. **Export functionality**: Save plot as PNG/PDF
2. **Multiple plots**: Separate windows for different node groups
3. **Statistical views**: Min/max/avg overlays
4. **Log scale**: Toggle for exponential growth/decay
5. **Pause/resume**: Freeze plot while graph continues
6. **Historical comparison**: Overlay multiple runs

## Code Quality
- ✅ Type hints used where appropriate
- ✅ Docstrings for all methods
- ✅ Error handling (empty graph, no nodes selected)
- ✅ Clean separation of concerns (dialog vs plot window)
- ✅ Integration with existing signal architecture

## Summary
The plotting feature is **fully functional** and ready to use. It seamlessly integrates with the existing GUI architecture and provides real-time visualization of node values during graph execution. Perfect for monitoring GA fitness, NN training loss, or any time-series node behavior.
