# Zorvan Visual Editor

A PyQt6-based graphical interface for creating, editing, and running computational graphs.

## Installation

```bash
pip install -r requirements_gui.txt
```

## Running the GUI

```bash
python run_new_ui.py
```

## Features

### Theming & Styling 🔧

- The GUI uses a singleton `ThemeManager` (see `gui_framework/legacy/theme.py`) to store colors, fonts and stylesheet fragments.
- Widgets that should react to theme changes should inherit from `ThemeMixin` (`gui_framework/legacy/theme_utils.py`; an MVVM-friendly variant lives in `gui_framework/widgets/theme_mixin.py`). `ThemeMixin` subscribes to `theme_changed` and calls an `apply_theme()` method which the widget implements to reapply colors/fonts/styles. This centralizes theme logic, avoids inline `setStyleSheet` duplication, and simplifies testing.


### 1. **Node Palette (Left Panel)**
Contains all available node types organized by category:

- **Activation Functions**: SigmoidNode, ReLUNode, LinearNode, GaussianNode, PiecewiseLinearNode, and their derivatives
- **Evolutionary Algorithm Nodes**: TournamentSelectionNode, CrossoverNode, MutationNode, DeJongSphereNode
- **Utility Nodes**: DisplayNode

### 2. **Graph Canvas (Center)**
Interactive workspace for building your computational graph:

- **Add Nodes**: Drag node types from the palette onto the canvas
- **Move Nodes**: Click and drag nodes to reposition them
- **Connect Nodes**:
  - Click on a node's output port (bottom white circle)
  - Drag to the input port (top white circle) of another node
  - Release to create the connection
   - **Multi-Node Connect**: Select multiple nodes (drag select or Ctrl+click). Hover near the outer edge of any selected node until a crosshair cursor appears; all selected nodes will glow yellow. Click and drag to a target node, and release to create connections from all selected nodes to the target (useful for building fan-in links quickly).
- **Select Nodes**: Click to select, drag to select multiple
- **Delete**: Select items and press `Delete` or `Backspace`
- **Zoom**: Use mouse wheel to zoom in/out
- **Pan**: Hold middle mouse button and drag (or use rubber band selection)

### 3. **Control Panel (Right Panel)**

#### Execution Controls
- **Play ▶**: Start continuous graph execution
- **Pause ⏸**: Pause execution
- **Step →**: Execute one step at a time
- **Reset ⏹**: Reset graph to initial state
- **Max Steps**: Set the maximum number of iterations
- **Speed Slider**: Adjust execution speed (10-2000 ms per step)
   - **Typed Speed**: You can also type an exact value for Speed (ms/step) using the new numeric input (spinbox) next to the slider. Values are kept in sync between the slider and the spinbox.

#### Visualization
- **Colorize by Value**: Enable heat map coloring of nodes
  - Blue = low values (cold)
  - Red = high values (hot)
 - **Colorize as ANN (toggle)**: Enable ANN-style color scheme for nodes (mutually exclusive with Colorize by Value)
- **Min/Max Values**: Set the color scale range

#### Layout Algorithms
- **Spring Layout**: Physics-based layout (good for general graphs)
- **Hierarchical Layout**: Layered layout (good for DAGs)
- **Circular Layout**: Nodes arranged in a circle
 - **Good Layout**: MLP-specific grid-based deterministic layout
 - **Good Layout (Dynamic)**: Improved Good Layout that automatically widens layer spacing for dense layers to maintain clarity and avoid collisions
 - **Good Layout (Dynamic per-layer)**: Improved Good Layout that adjusts spacing per-layer while keeping columns for different layers aligned; less disruptive for manual layouts
 - **Good Layout (Divide & Conquer)**: New layout that first places forward-pass nodes and then places backprop/weight/buffer nodes relative to their predecessors. Uses a grid-based cell system and per-layer dynamic spacing with clamping to prevent drastic movement.
 - **Final Layout**: Deterministic MLP & Backprop layout implementing the complete 'The final Layout' rules (name based detection, topology fallback, grid-based column/row placement, and placement tracking to avoid rearranging nodes).

### 4. **Menu Bar**

#### File Menu
- **New**: Create a new empty graph
- **Open**: Load a graph from file
- **Save**: Save current graph to file — legacy Draw.io (.drawio/.xml) export is deprecated. Use CGJson (.cgjson/.cgz) for supported graph persistence.
- **Exit**: Close the application

#### Edit Menu
- **Delete**: Remove selected items
- **Edit Node**: Open property editor for selected node (Ctrl+E)
 - **Copy/Cut/Paste**: Copy and paste selected nodes (Ctrl+C / Ctrl+X / Ctrl+V). Paste centers pasted nodes in view and recreates internal edges between copied nodes.

#### View Menu
- Toggle visibility of Node Palette and Control Panel

### 5. **Processing Modes**
Choose the processor type in the control panel:
- **Concurrent** (main mode): each step, every node reads a snapshot of the graph and then updates; a signal moves one node per step.
- **Forward Processing** (experimental): runs nodes along data dependencies from the configured starting nodes; stopping nodes cut the sequence.
- **Manual Processing** (experimental): runs a hand-picked node sequence.

### 6. **Graph Simplification**
Large graphs can be viewed at coarser granularity without changing results:
- **Compress Selection** (node context menu): collapse a chain into a compressed node; **Decompress Node** reverses it.
- **Abstract**: group parallel nodes that share the same inputs and outputs into an abstract node; expanding restores them.
- **Simplify Step / Expand Step** (control panel): apply or undo one step of the automatic simplification algorithm.

Compressed and abstract nodes behave exactly like the nodes they contain, tick for tick. They are a view, not a different computation.

## Keyboard Shortcuts

- `Ctrl+N` - New graph
- `Ctrl+O` - Open graph
- `Ctrl+S` - Save graph
- `Ctrl+E` - Edit selected node
- `Delete` - Delete selected items
- `Ctrl+Q` - Quit application
 - `Ctrl+C` - Copy selected node(s)
 - `Ctrl+V` - Paste copied node(s)
 - `Ctrl+X` - Cut selected node(s)

## Editing Node Properties

1. Select a node
2. Press `Ctrl+E` or use Edit → Edit Node
3. Modify properties in the dialog:
   - **Name**: Change the node's display name
   - **Type-specific properties**:
     - DataStreamNode: Edit the data sequence
     - BufferNode: Set buffer size
     - ListNode: Toggle allowNone
     - GaussianNode: Set mean and std deviation
     - LinearNode: Set slope and intercept
     - Arithmetic nodes: Set initial value

## Workflow Example

1. **Build the Graph**:
   - Drag a `DataStreamNode` onto the canvas
   - Drag an `AdditionNode` next to it
   - Connect DataStream output → Addition input
   - Edit DataStream to set your data sequence

2. **Configure Execution**:
   - Set Max Steps (e.g., 10)
   - Adjust Speed slider if needed
   - Enable "Colorize by Value" to see visual feedback

3. **Run**:
   - Click Play ▶
   - Watch nodes update in real-time
   - Node circles show current values
   - Colors indicate value ranges

4. **Analyze**:
   - Pause execution to inspect values
   - Use Step button to advance one iteration
   - Reset and modify parameters

## Tips

- **Start Simple**: Begin with a DataStreamNode → AdditionNode connection to understand the flow
- **Use Display Nodes**: Add DisplayNode to print values to console during execution
- **Organize with Layouts**: Use auto-layout buttons to clean up messy graphs
- **Save Often**: Use File → Save (`.cgjson` / `.cgz`) to preserve your work
- **Experiment**: Try different node combinations to build complex computational pipelines

## Node Categories Explained

### Data Nodes
Provide or store data throughout the graph execution:
- **DataStreamNode**: Iterates through a predefined list of values
- **BufferNode**: Maintains a sliding window of recent values
- **ListNode**: Collects multiple inputs into a single list

### Arithmetic Nodes
Perform mathematical operations on inputs:
- **AdditionNode**: Sums all inputs
- **MultiplicationNode**: Multiplies all inputs
- **SubtractionNode**: Subtracts inputs
- **DivisionNode**: Divides inputs

### Activation Functions
Apply non-linear transformations (useful for neural networks):
- **SigmoidNode**: S-curve activation (0 to 1)
- **ReLUNode**: Rectified Linear Unit (max(0, x))
- **LinearNode**: Linear transformation (y = mx + b)
- **GaussianNode**: Gaussian/bell curve

### Evolutionary Nodes
Support genetic algorithm implementations:
- **TournamentSelectionNode**: Tournament selection for EA
- **CrossoverNode**: Genetic crossover operation
- **MutationNode**: Genetic mutation operation

### Fuzzy Logic Nodes
Build fuzzy inference systems:
- **PiecewiseLinearNode**: Piecewise linear membership function
- **GaussianMembershipNode**: Gaussian membership (inputs: value, center, sigma, in that order)
- **MinNode / MaxNode**: Fuzzy AND / OR

### Structure Nodes
- **ContainerNode**: Holds a value that accumulates updates (e.g. trainable weights)
- **CompressedNode / AbstractNode**: Complex nodes created by simplification

Note: node inputs are **ordered** by the order connections were made. For nodes where position matters (e.g. GaussianMembership, Subtraction, Division), connect inputs in the expected order.

## Troubleshooting

**GUI doesn't start**:
- Ensure PyQt6 is installed: `pip install PyQt6`
- Check Python version (3.10 or 3.11 are tested in CI)

**Nodes don't connect**:
- Make sure you're dragging from output port (bottom) to input port (top)
- Release mouse button when hovering over the target port

**Graph doesn't run**:
- Check that all nodes are properly connected
- Verify DataStreamNodes have valid data
- Look for error messages in the status bar

**Layout algorithms don't work**:
- Install networkx: `pip install networkx`

## Feature Status

- [x] Save/Load graphs (`.cgjson` / `.cgz`)
- [x] Undo/Redo for core canvas edits
- [x] Copy/Paste nodes
- [x] Node grouping (compression, abstraction, subgraphs)
- [x] Real-time plotting of node values
- [x] Custom node creation interface
- [ ] Breakpoints for debugging
- [ ] Export graph as image

The next major UI is planned as a TypeScript/WebGL editor with a Tauri desktop app (see `docs/REARCHITECTURE_PLAN.md`, Phase 5). The PyQt editor remains the supported UI until that reaches feature parity.

## Contributing

- Prefer fixes and parity work over large new PyQt features (the UI will be replaced; see above).
- To add node types or editors:
  1. Add the node type to `gui_framework/legacy/node_registry.py`.
  2. Make sure the canvas can instantiate it (`gui_framework/legacy/graph_canvas.py`, drop handling).
  3. Add type-specific editors in the node editor dialog (`gui_framework/views/node_editor_dialog.py`).
- Include tests and doc updates with every change (`CONTRIBUTING.md`).

## Headless GUI tests (CI)

- CI runs a GUI smoke job (`gui-smoke` in `.github/workflows/ci.yml`) with an offscreen Qt platform under Xvfb. Some Windows-unstable GUI tests are currently skipped.
- To run GUI tests headless locally:

  ```bash
  # Linux: install Xvfb, then
  export QT_QPA_PLATFORM=offscreen
  xvfb-run -a python -m pytest Tests/gui_tests/integration -q
  ```

- `Tests/gui_tests/integration/startup/test_gui_smoke.py` checks that the `MainWindow` can be constructed in offscreen mode.

---

**License**: MIT (see `LICENSE`)
